"""Resolve literal Artemis AST scene/label references without executing macros."""
import argparse,hashlib,json
from pathlib import Path
from parse_ast_tables import parse

def scan(root):
    scenes=[];checks=[];references=[]
    for p in sorted(root.rglob('*.ast')):
        try:
            a=parse(p.read_text('utf-8-sig'),True)
            blocks={k:v for k,v in a.items() if isinstance(k,int) and isinstance(v,dict)}
            labels=a.get('label',{})
            info={'path':str(p),'scene':p.stem,'archive_group':str(p.parent),'blocks':sorted(blocks),'labels':labels}
            scenes.append(info)
            for k,b in blocks.items():
                for index,c in b.items():
                    if not isinstance(index,int) or not isinstance(c,dict):continue
                    command=c.get(1)
                    if command in ('excall','call','jump','goto','select'):
                        label=c.get('label');meta=labels.get(label)
                        target=meta.get('block') if isinstance(meta,dict) else meta
                        references.append({'source':str(p),'block':k,'command_index':index,'command':command,'arguments':c,
                            'scene_literal':c.get('file'),'label_literal':label,
                            'local_target_block':target if target in blocks else None,
                            'kind':'literal-reference; macro-execution-unverified'})
            checks.append({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'passed':True})
        except Exception as ex:checks.append({'source':str(p),'passed':False,'error':str(ex)})
    for ref in references:
        target=ref['scene_literal']
        if not isinstance(target,str):continue
        # Never merge same-name files from different extracted archives.
        candidates=[s for s in scenes if s['archive_group']==str(Path(ref['source']).parent) and s['scene']==Path(target).stem]
        ref['scene_candidates']=[s['path'] for s in candidates]
        ref['target_status']='unique-literal-scene' if len(candidates)==1 else 'unresolved-or-ambiguous'
        if len(candidates)==1 and ref['label_literal']:
            ref['target_label_metadata']=candidates[0]['labels'].get(ref['label_literal'])
    return {'scenes':scenes,'references':references,'checks':checks,'story_complete':False,'runtime_verified':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    r=scan(a.input);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print(json.dumps({'scenes':len(r['scenes']),'references':len(r['references']),'resolved_scenes':sum(x.get('target_status')=='unique-literal-scene' for x in r['references'])}))
if __name__=='__main__':main()
