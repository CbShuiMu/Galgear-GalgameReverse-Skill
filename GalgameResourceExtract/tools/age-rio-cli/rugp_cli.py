"""Read-only rUGP raster extraction and explicit, uninstalled RUO round-trip tools.

Codec/RUO source: pinned AgeReVerse (MIT), retained under source/ with LICENSE.
No game discovery, installation, name recovery or complete-CG claim.
"""
from __future__ import annotations
import argparse,collections,dataclasses,hashlib,json,mmap,pathlib,sys,time
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'source'))
from rUGP.formats.images.cr6ti_decode import parse_standard_cr6ti_record,png_rgba_bytes
from rUGP.formats.images.crip008_decode import parse_crip008_header
from rUGP.tools.images.decode_record import decode_record,read_exact_extent
from rUGP.formats.images.cr6ti_reference import decode_record as native_reference

MAX_PIXELS=16777216;MAX_BYTES=16*1024*1024
LEGACY_CR6TI_PROFILE='legacy-serialized-cr6ti'
LEGACY_CR6TI_KINDS={
    b'\x02\x06\x81\x00\x07', b'\x02\x06\x81\x00\x0f',
    b'\x03\x03\x81\x00\x07', b'\x03\x03\x81\x00\x0f',
}
def digest(b):return hashlib.sha256(b).hexdigest()
def dump(p,value):
    with pathlib.Path(p).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def norm(p):return pathlib.Path(p).resolve()
def fresh(p):
    p=norm(p)
    if p.exists():raise ValueError('output already exists')
    p.parent.mkdir(parents=True,exist_ok=True);return p
def safe_header(record,codec):
    if codec in ('cr6ti','crip008'):
        h=parse_standard_cr6ti_record(record) if codec=='cr6ti' else parse_crip008_header(record)
        if not 0<h.width*h.height<=MAX_PIXELS:raise ValueError('pixel safety limit')
        return dataclasses.asdict(h)
    return {}
def legacy_cr6ti_header(record):
    return (len(record)>=46 and record[0]&3==0 and record[1]&0xc0==0xc0
            and record[2:6]==b'\x45\0\0\0' and record[18:23] in LEGACY_CR6TI_KINDS)
def image_decode_record(record,codec,profile=None):
    if profile is None:return record
    if profile!=LEGACY_CR6TI_PROFILE or codec!='cr6ti' or not legacy_cr6ti_header(record):
        raise ValueError('image profile does not match the raw header')
    return b'\x00\x04'+record[2:]
def decode_native(record,codec,profile=None):
    record=image_decode_record(record,codec,profile)
    header=safe_header(record,codec)
    if codec=='cr6ti':
        result=native_reference(record)
        return result.header.width,result.header.height,result.rgba,{**header,'decoder':'native-reference; combined kind3 clamp and cleared transparent predictors'}
    return decode_record(record,codec)
def scan(sources,output,legacy_cr6ti=False):
    output=fresh(output);rows=[];stats=[]
    marker=b'\x45\0\0\0' if legacy_cr6ti else b'\x00\x04\x45'
    marker_offset=2 if legacy_cr6ti else 0
    profile=LEGACY_CR6TI_PROFILE if legacy_cr6ti else None
    for source in sources:
        source=norm(source);count=0
        with source.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
            at=0
            while True:
                at=b.find(marker,at)
                if at<0:break
                pos=at-marker_offset;at+=1;count+=1
                if pos<0:continue
                h=b[pos:pos+48]
                if len(h)<48 or (legacy_cr6ti and not legacy_cr6ti_header(h)):continue
                w=int.from_bytes(h[6:8],'little');height=int.from_bytes(h[8:10],'little')
                if not 0<w<=8192 or not 0<height<=8192 or w*height>MAX_PIXELS or h[18] not in (2,3):continue
                options=[]
                layouts=[('cr6ti',int.from_bytes(h[32:36],'little')+46)]
                if not legacy_cr6ti:layouts.append(('crip008',int.from_bytes(h[29:33],'little')+41))
                for codec,extent in layouts:
                    if not 48<extent<=MAX_BYTES or pos+extent>len(b):continue
                    try:
                        header=safe_header(image_decode_record(b[pos:pos+extent],codec,profile),codec)
                        if codec=='crip008' and (header['header_version'] not in (0,129) or header['compress_flags']&~7 or any(header[k] not in range(5,9) for k in ('b_bits','g_bits','r_bits'))):continue
                        option={'codec':codec,'extent':extent,'header':header}
                        if profile:option['profile']=profile
                        options.append(option)
                    except ValueError:continue
                if options:rows.append({'source':str(source),'offset':pos,'options':options,'identity':'header-candidate; directory/owner not inferred'})
        stats.append({'source':str(source),'size':source.stat().st_size,'mtime_ns':source.stat().st_mtime_ns,'magic_hits':count})
    dump(output,{'schema':'rugp-header-candidates/1','sources':stats,'candidates':rows,'cg_complete':False});return {'candidates':len(rows)}
def extract(index,root,output):
    output=fresh(output);root=norm(root);data=json.loads(pathlib.Path(index).read_text('utf-8'));prepared=[]
    for i,r in enumerate(data['candidates']):
        source=norm(r['source'])
        if not source.is_relative_to(root):raise ValueError('source outside explicit root')
        for j,o in enumerate(r['options']):
            if o['codec'] not in ('cr6ti','crip008','crip007','crmt'):raise ValueError('unknown codec')
            if not 0<o['extent']<=MAX_BYTES:raise ValueError('record limit')
            prepared.append((i,j,r,o,source))
    output.mkdir()
    with (output/'manifest.jsonl').open('x',encoding='utf-8') as f:
        for i,j,r,o,source in prepared:
            raw=read_exact_extent(source,r['offset'],o['extent'])
            safe_header(image_decode_record(raw,o['codec'],o.get('profile')),o['codec'])
            rel=source.name+'/'+f'{i:06d}-{r["offset"]:012x}-{j}-{o["codec"]}.bin';p=output/rel;p.parent.mkdir(exist_ok=True)
            with p.open('xb') as w:w.write(raw)
            row={'kind':'raw','id':f'{i:06d}-{j}','relative_path':rel,'source':str(source),'offset':r['offset'],'extent':len(raw),'codec':o['codec'],'sha256':digest(raw),'header':o.get('header',{}),'identity':r.get('identity','index-supplied')}
            if 'profile' in o:row['profile']=o['profile']
            f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
    return {'raw_records':len(prepared)}
def decode_tree(raw_root,output,limit=None):
    raw_root=norm(raw_root);output=fresh(output);output.mkdir();counts=collections.Counter();start=time.monotonic()
    with (output/'manifest.jsonl').open('x',encoding='utf-8') as log, (raw_root/'manifest.jsonl').open(encoding='utf-8') as inputs:
        for i,line in enumerate(inputs):
            if limit is not None and i>=limit:break
            r=json.loads(line);p=(raw_root/r['relative_path']).resolve()
            if not p.is_relative_to(raw_root):raise ValueError('raw path outside root')
            try:
                raw=p.read_bytes()
                if digest(raw)!=r['sha256']:raise ValueError('raw hash differs')
                w,h,rgba,header=decode_native(raw,r['codec'],r.get('profile'));png=png_rgba_bytes(w,h,rgba)
                dest=output/(r['relative_path']+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as f:f.write(png)
                r.update(kind='png',png_relative_path=dest.relative_to(output).as_posix(),png_sha256=digest(png),rgba_sha256=digest(rgba),width=w,height=h,header=header,transparent_pixels=sum(a==0 for a in rgba[3::4]),partial_alpha_pixels=sum(0<a<255 for a in rgba[3::4]))
                counts['decoded']+=1
            except Exception as e:r.update(kind='decode_error',error=str(e));counts['failed']+=1
            log.write(json.dumps(r,ensure_ascii=False)+'\n');log.flush()
            if (i+1)%100==0:print(json.dumps({'processed':i+1,**counts}),flush=True)
    result={'counts':dict(counts),'seconds':time.monotonic()-start,'cg_complete':False,'game_verified':False};dump(output/'summary.json',result);return result
def encode(template,rgba_path,output,allow_quantization=False):
    from rUGP.formats.images.cr6ti_encode import encode_cr6ti
    from rUGP.formats.images.cr6ti_reference import decode_record as reference
    output=fresh(output);fresh(output.with_suffix(output.suffix+'.json'));raw=pathlib.Path(template).read_bytes();header=safe_header(raw,'cr6ti')
    if pathlib.Path(rgba_path).suffix.lower()=='.png':
        from rUGP.formats.images.crip008_kind2_encode import read_png_rgba
        w,h,pixels=read_png_rgba(pathlib.Path(rgba_path))
        if (w,h)!=(header['width'],header['height']):raise ValueError('PNG dimensions differ from template')
    else:pixels=pathlib.Path(rgba_path).read_bytes()
    original=decode_native(raw,'cr6ti')[2]
    if pixels==original:
        record,expected,stats=raw,original,{'strategy':'unchanged RGBA; preserve original serialized bytes'}
    else:record,expected,stats=encode_cr6ti(raw,pixels)
    actual=reference(record).rgba
    if actual!=expected:raise ValueError('independent pixel readback differs')
    if actual!=pixels and not allow_quantization:raise ValueError('encoder changes input pixels; strict output refused; explicit --allow-quantization is required for a lossy candidate')
    with output.open('xb') as f:f.write(record)
    report={'codec':'cr6ti','record_sha256':digest(record),'input_rgba_sha256':digest(pixels),'decoded_rgba_sha256':digest(actual),'input_pixels_exact':pixels==actual,'independent_readback_passed':True,'stats':stats,'game_verified':False}
    dump(output.with_suffix(output.suffix+'.json'),report);return report
def overlay(record,source_offset,unit,output,base=None):
    from rUGP.formats.rio.crypto import encode_extent_offset,decode_extent_offset,decode_extent_size
    from rUGP.formats.rio.ruo import build_ruo,read_footer
    output=fresh(output);fresh(output.with_suffix(output.suffix+'.json'));raw=pathlib.Path(record).read_bytes();key=encode_extent_offset(source_offset,unit)
    # Upstream writer is guarded here because it otherwise permits overwriting.
    report=build_ruo(output,unit,[(key,raw)],base_ruo=pathlib.Path(base) if base else None)
    table,redirects=read_footer(output,unit);entry=next(r for r in redirects if r.source_raw_offset==key)
    at=decode_extent_offset(entry.ruo_raw_offset,unit);extent=decode_extent_size(entry.replacement_raw_size)
    with output.open('rb') as f:f.seek(at);reread=f.read(extent)
    if reread!=raw:raise ValueError('RUO replacement readback differs')
    report.update(replacement_readback_passed=True,installed=False,game_verified=False)
    if base:
        old_end,old=read_footer(pathlib.Path(base),unit)
        with pathlib.Path(base).open('rb') as a,output.open('rb') as b:
            if a.read(old_end)!=b.read(old_end):raise ValueError('base data changed')
        after={r.source_raw_offset:r for r in redirects}
        if any(after[r.source_raw_offset]!=r for r in old if r.source_raw_offset!=key):raise ValueError('inherited redirect changed')
        report['inherited_data_and_redirects_unchanged']=True
    dump(output.with_suffix(output.suffix+'.json'),report);return report
def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('scan');a.add_argument('output');a.add_argument('sources',nargs='+');a.add_argument('--legacy-cr6ti',action='store_true')
    a=s.add_parser('extract');a.add_argument('index');a.add_argument('root');a.add_argument('output')
    a=s.add_parser('decode-tree');a.add_argument('raw_root');a.add_argument('output');a.add_argument('--limit',type=int)
    a=s.add_parser('encode-cr6ti');a.add_argument('template');a.add_argument('rgba');a.add_argument('output');a.add_argument('--allow-quantization',action='store_true')
    a=s.add_parser('overlay');a.add_argument('record');a.add_argument('output');a.add_argument('--source-offset',type=lambda v:int(v,0),required=True);a.add_argument('--unit',type=int,required=True);a.add_argument('--base')
    args=p.parse_args()
    try:
        if args.command=='scan':r=scan(args.sources,args.output,args.legacy_cr6ti)
        elif args.command=='extract':r=extract(args.index,args.root,args.output)
        elif args.command=='decode-tree':r=decode_tree(args.raw_root,args.output,args.limit)
        elif args.command=='encode-cr6ti':r=encode(args.template,args.rgba,args.output,args.allow_quantization)
        else:r=overlay(args.record,args.source_offset,args.unit,args.output,args.base)
        print(json.dumps(r,ensure_ascii=False));return 1 if r.get('counts',{}).get('failed',0) else 0
    except Exception as e:print(json.dumps({'passed':False,'error':str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
