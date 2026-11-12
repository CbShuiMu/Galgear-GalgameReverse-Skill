"""Synthetic profile, native-pixel, cumulative overlay and input boundary checks."""
import pathlib,sys,tempfile,unittest,json,subprocess,shutil,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];TOOL=ROOT/'GalgameResourceExtract/tools/age-rio-cli'
sys.path.insert(0,str(TOOL));import rugp_cli as cli
from rUGP.formats.images.cr6ti_encode import encode_cr6ti
from rUGP.formats.images.cr6ti_reference import decode_record as reference
from rUGP.formats.rio.crypto import decode_extent_offset,decode_extent_size
from rUGP.formats.rio.ruo import read_footer
def sample(kind=3):
 h=bytearray(44);h[:3]=b'\0\x04E';h[6:8]=(4).to_bytes(2,'little');h[8:10]=(2).to_bytes(2,'little');h[14:16]=(4).to_bytes(2,'little');h[16:18]=(2).to_bytes(2,'little');h[18]=kind;h[19]=3;h[22]=7
 rgba=bytes([20,40,60,255,80,100,120,128,0,0,0,0,20,40,60,255]*2)
 if kind==2:rgba=bytes([20,40,60,255]*8)
 raw,pixels,_=encode_cr6ti(bytes(h)+b'\0\0',rgba);return raw,pixels
class Images(unittest.TestCase):
 def test_supported_profiles_and_independent_pixels(self):
  for kind in (2,3):
   raw,pixels=sample(kind);w,h,actual,meta=cli.decode_native(raw,'cr6ti');self.assertEqual((w,h),(4,2));self.assertEqual(actual,pixels);self.assertEqual(reference(raw).rgba,pixels)
   for bad in (raw[:-1],raw+b'\0',raw[:20]):
    with self.assertRaises(ValueError):cli.decode_record(bad,'cr6ti')
 def test_scan_raw_decode_and_tamper_detection(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);raw,pixels=sample();source=d/'test.rio';source.write_bytes(bytes(8)+raw);index=d/'index.json';cli.scan([source],index)
   self.assertEqual(len(json.loads(index.read_text())['candidates']),1);cli.extract(index,d,d/'raw');r=cli.decode_tree(d/'raw',d/'png');self.assertEqual(r['counts'],{'decoded':1})
   p=next((d/'raw').rglob('*.bin'));p.write_bytes(p.read_bytes()+b'x');r=cli.decode_tree(d/'raw',d/'failed');self.assertEqual(r['counts'],{'failed':1})
 def test_legacy_cr6ti_profile_preserves_original_prefix(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td)
   standard,pixels=sample()
   native=bytearray(standard);native[:2]=b'\x40\xc0';native[20]=0x81
   invalid=bytearray(native);invalid[1]=0x80
   source=d/'test.rio';source.write_bytes(bytes(8)+native+invalid)
   cli.scan([source],d/'normal.json')
   self.assertFalse(json.loads((d/'normal.json').read_text())['candidates'])
   cli.scan([source],d/'legacy.json',legacy_cr6ti=True)
   candidates=json.loads((d/'legacy.json').read_text())['candidates']
   self.assertEqual([row['offset'] for row in candidates],[8])
   cli.extract(d/'legacy.json',d,d/'raw')
   row=json.loads((d/'raw/manifest.jsonl').read_text())
   extracted=(d/'raw'/row['relative_path']).read_bytes()
   self.assertEqual(extracted,native)
   self.assertEqual(cli.decode_native(extracted,'cr6ti',row['profile'])[2],pixels)
   self.assertEqual(cli.decode_tree(d/'raw',d/'png')['counts'],{'decoded':1})
 def test_kind3_shared_delta_clamps_only_after_residual(self):
  template,_=sample(3);pixels=bytes([254,0,254,255,254,254,254,255]*4);raw,expected,_=encode_cr6ti(template,pixels)
  self.assertEqual(expected,pixels);self.assertEqual(cli.decode_native(raw,'cr6ti')[2],pixels)
 def test_identity_encoding_preserves_original_record_bytes(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);raw,pixels=sample();src=d/'image.bin';src.write_bytes(raw);png=d/'input.png';png.write_bytes(cli.png_rgba_bytes(4,2,pixels));report=cli.encode(src,png,d/'new.bin');self.assertTrue(report['input_pixels_exact']);self.assertEqual((d/'new.bin').read_bytes(),raw)
 def test_transparent_row_clears_above_row_rgb(self):
  raw,_=sample();h=bytearray(raw[:44]);h[8:10]=(3).to_bytes(2,'little');h[16:18]=(3).to_bytes(2,'little');h[32:36]=bytes(4)
  pixels=bytes([100,60,20,255]*4+[0,0,0,0]*4+[0,0,0,255]*4);record,expected,_=encode_cr6ti(bytes(h)+b'\0\0',pixels)
  self.assertEqual(expected,pixels);self.assertEqual(cli.decode_native(record,'cr6ti')[2],pixels)
 def test_lossy_encoder_requires_explicit_option(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);raw,_=sample(2);src=d/'image.bin';src.write_bytes(raw);png=d/'input.png';png.write_bytes(cli.png_rgba_bytes(4,2,bytes([255,255,255,255]*8)))
   with self.assertRaises(ValueError):cli.encode(src,png,d/'strict.bin')
   self.assertFalse((d/'strict.bin').exists());r=cli.encode(src,png,d/'allowed.bin',True);self.assertFalse(r['input_pixels_exact']);self.assertTrue(r['independent_readback_passed'])
 def test_cumulative_ruo_preserves_existing_entries_and_data(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);raw,_=sample();record=d/'r.bin';record.write_bytes(raw);cli.overlay(record,20,2,d/'base.ruo1');before=(d/'base.ruo1').read_bytes();cli.overlay(record,40,2,d/'new.ruo1',d/'base.ruo1')
   end,old=read_footer(d/'base.ruo1',2);after,entries=read_footer(d/'new.ruo1',2);self.assertEqual(len(entries),2);self.assertEqual((d/'new.ruo1').read_bytes()[:end],before[:end]);self.assertEqual((d/'base.ruo1').read_bytes(),before)
   for e in entries:
    at=decode_extent_offset(e.ruo_raw_offset,2);size=decode_extent_size(e.replacement_raw_size);self.assertEqual((d/'new.ruo1').read_bytes()[at:at+size],raw)
   cli.overlay(record,20,2,d/'replace.ruo1',d/'new.ruo1');self.assertEqual(len(read_footer(d/'replace.ruo1',2)[1]),2)
   with self.assertRaises(ValueError):cli.overlay(record,20,2,d/'base.ruo1')
 def test_independent_install_and_source_root_rejection(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);installed=d/'installed';shutil.copytree(TOOL,installed,ignore=shutil.ignore_patterns('__pycache__'))
   raw,_=sample();source=d/'outside.rio';source.write_bytes(raw);index=d/'index.json';cli.scan([source],index);root=d/'game';root.mkdir()
   with self.assertRaises(ValueError):cli.extract(index,root,d/'reject')
   p=subprocess.run([sys.executable,str(installed/'rugp_cli.py'),'scan',str(d/'isolated.json'),str(source)],cwd=d,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_pack_cli_independent_pixel_and_overlay_roundtrip(self):
  tool=ROOT/'GalgameResourcePack/tools/age-rio-cli'
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);installed=d/'pack';shutil.copytree(tool,installed,ignore=shutil.ignore_patterns('__pycache__'));raw,pixels=sample();src=d/'raw.bin';src.write_bytes(raw);png=d/'input.png';png.write_bytes(cli.png_rgba_bytes(4,2,pixels))
   for args in (['encode-cr6ti',src,png,d/'encoded.bin'],['overlay',d/'encoded.bin',d/'new.ruo1','--source-offset','20','--unit','2']):
    r=subprocess.run([sys.executable,str(installed/'rugp_cli.py'),*[str(a) for a in args]],cwd=d,capture_output=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual((d/'encoded.bin').read_bytes(),raw);self.assertEqual(len(read_footer(d/'new.ruo1',2)[1]),1);self.assertTrue((installed/'LICENSE').is_file())
if __name__=='__main__':unittest.main()
