"""Synthetic CG export boundaries: raw identity, multiple frames, paths and audit."""
import pathlib,sys,json,struct,zlib,tempfile,subprocess,zipfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];SK=ROOT/'GalgameResourceExtract'
sys.path.insert(0,str(SK/'scripts'))
from cg_inventory import audit
CLI=SK/'tools/GARbro-cli/legacy/GalImageExport.exe'
def png():
 def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes([0,10,20,30,123])))+chunk(b'IEND',b'')
def g00():
 def frame(pixel):return struct.pack('<HH',1,1)+bytes(0x70)+struct.pack('<HHhHH',0,0,0,1,1)+bytes(0x52)+pixel
 a=frame(bytes([1,2,3,255]));b=frame(bytes([4,5,6,123]));data=struct.pack('<IIIII',2,20,len(a),20+len(a),len(b))+a+b
 packed=b''.join(b'\xff'+data[i:i+8] for i in range(0,len(data),8))
 return struct.pack('<BHHI',2,2,1,2)+struct.pack('<6i',0,0,0,0,0,0)+struct.pack('<6i',1,0,0,0,0,0)+struct.pack('<II',len(packed)+8,len(data))+packed
@unittest.skipUnless(sys.platform=='win32' and CLI.exists(),'Windows GameRes image CLI required')
class ImageExport(unittest.TestCase):
 def run_job(self,root,job):
  p=root/'job.json';p.write_text(json.dumps(job),encoding='utf-8');r=subprocess.run([str(CLI),str(p)],capture_output=True,timeout=25);self.assertEqual(r.returncode,0,r.stderr);return pathlib.Path(job['output'])/'manifest.jsonl'
 def test_raw_alpha_and_multiframe(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);a=root/'a.png';a.write_bytes(png());b=root/'frames.g00';b.write_bytes(g00());out=root/'result'
   manifest=self.run_job(root,{'mode':'files','source':str(root),'files':[str(a),str(b)],'output':str(out),'seconds':20})
   rows=[json.loads(x) for x in manifest.read_text('utf-8').splitlines()];self.assertEqual((out/'raw/a.png').read_bytes(),a.read_bytes());self.assertEqual((out/'raw/frames.g00').read_bytes(),b.read_bytes())
   self.assertEqual(sum(x['kind']=='png' for x in rows),3);self.assertEqual(sum(x.get('frames',0) for x in rows),2)
   encoded=(out/'png/a.png.png').read_bytes();self.assertEqual(encoded[25],6)
   cursor=8;payload=b''
   while cursor<len(encoded):
    length=struct.unpack_from('>I',encoded,cursor)[0];tag=encoded[cursor+4:cursor+8]
    if tag==b'IDAT':payload+=encoded[cursor+8:cursor+8+length]
    cursor+=length+12
   self.assertEqual(zlib.decompress(payload)[-1],123)
   result=audit([manifest],True);self.assertTrue(result['passed'],result['errors']);self.assertEqual(result['raw_files'],2)
   (out/'raw/a.png').write_bytes(b'changed');self.assertFalse(audit([manifest],True)['passed'])
 def test_archive_traversal_does_not_escape(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);p=root/'test.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('../escape.png',png());z.writestr('safe.png',png())
   manifest=self.run_job(root,{'mode':'archive','source':str(p),'output':str(root/'out'),'seconds':20,'all':True})
   rows=[json.loads(x) for x in manifest.read_text('utf-8').splitlines()];self.assertTrue(any(x['kind']=='raw_error' for x in rows));self.assertFalse((root/'out/escape.png').exists());self.assertTrue((root/'out/raw/safe.png').exists())
 def test_duplicate_archive_names_preserve_each_member(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);p=root/'duplicate.zip'
   import warnings
   with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    with zipfile.ZipFile(p,'w') as z:z.writestr('same.png',png());z.writestr('same.png',png())
   manifest=self.run_job(root,{'mode':'archive','source':str(p),'output':str(root/'out'),'seconds':20,'all':True})
   rows=[json.loads(x) for x in manifest.read_text('utf-8').splitlines()];raw=[x for x in rows if x['kind']=='raw'];self.assertEqual(len(raw),2);self.assertEqual(len({x['path'] for x in raw}),2);self.assertEqual([x['original_name'] for x in raw],['same.png','same.png']);self.assertTrue(raw[1]['duplicate_name'])
if __name__=='__main__':unittest.main()
