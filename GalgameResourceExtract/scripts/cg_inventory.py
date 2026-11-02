"""Audit raw images and PNG derivatives from GalImageExport JSONL manifests.

No deduplication, image composition or semantic CG classification is performed.
"""
import argparse,collections,hashlib,json,struct
from pathlib import Path

def file_hash(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

def audit(manifests,verify_hashes=False):
    raw={};png={};dependencies={};errors=[];counts=collections.Counter();frames=[]
    for source in manifests:
        with source.open(encoding='utf-8-sig') as f:
            for line_no,line in enumerate(f,1):
                try:r=json.loads(line)
                except ValueError:
                    errors.append({'source':str(source),'line':line_no,'error':'invalid JSON record'});continue
                kind=r.get('kind');counts[kind]+=1
                if kind=='frame_container':frames.append(r)
                if kind not in ('raw','ypf_raw_evidence','dat_raw_evidence','png','raw_dependency'):continue
                p=Path(r['path'])
                if not p.is_file():errors.append({'path':str(p),'error':'missing output'});continue
                if r.get('size') is not None and p.stat().st_size!=r['size']:errors.append({'path':str(p),'error':'size differs'})
                if verify_hashes and file_hash(p)!=r.get('sha256'):errors.append({'path':str(p),'error':'hash differs'})
                if kind=='png':
                    with p.open('rb') as image:head=image.read(24)
                    if len(head)!=24 or head[:8]!=b'\x89PNG\r\n\x1a\n':errors.append({'path':str(p),'error':'PNG header differs'})
                    elif struct.unpack('>II',head[16:24])!=(r['width'],r['height']):errors.append({'path':str(p),'error':'PNG dimensions differ'})
                    target=png
                else:target=dependencies if kind=='raw_dependency' else raw
                key=str(p.resolve())
                if key in target and target[key].get('sha256')!=r.get('sha256'):errors.append({'path':str(p),'error':'conflicting source records'})
                target[key]=r
    return {'passed':not errors,'raw_files':len(raw),'raw_dependencies':len(dependencies),'png_outputs':len(png),'raw_bytes':sum(Path(p).stat().st_size for p in raw),'png_bytes':sum(Path(p).stat().st_size for p in png),
        'record_counts':dict(counts),'frame_containers':len(frames),'declared_nonempty_frames':sum(r['frames'] for r in frames),'hashes_checked':verify_hashes,
        'errors':errors,'decode_errors':counts['decode_error'],'raw_errors':counts['raw_error'],'deferred':sum(counts[k] for k in ('raw_deferred','decode_deferred','archive_deferred')),
        'cg_semantic_complete':False,'all_differences_verified':False,'note':'Counts are physical files, including differences/layers and non-CG graphics; original inputs and decoder metadata remain authoritative.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--verify-hashes',action='store_true');a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    manifests=[a.input] if a.input.is_file() else sorted(a.input.glob('part-*/manifest.jsonl'))+sorted(a.input.glob('custom-manifest.jsonl'))
    if not manifests:ap.error('no manifests found')
    r=audit(manifests,a.verify_hashes);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':r['passed'],'raw':r['raw_files'],'png':r['png_outputs'],'errors':len(r['errors'])}));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
