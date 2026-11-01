"""Read Siglus messages, pending explicit names and conservative local CFG.
Uses the bundled SSSU 0.5.7 source; no game code is executed.
"""
from pathlib import Path
import collections,sys,json,hashlib
SSSU=Path(__file__).resolve().parents[1]/'tools/siglus-ssu/source'

def parse_scene(p,scene,variant='input'):
    sys.path.insert(0,str(SSSU));from siglus_ssu import dat
    bundle=dat.dat_disassembly_bundle(p.read_bytes(),str(p),scene_name=scene,emit_text=False)
    if not bundle or not bundle['complete']:raise ValueError('SSSU did not completely decode bytecode')
    tr=bundle['trace'];ofs={e['ofs']:i for i,e in enumerate(tr)};leaders={0};unresolved=[];edges=[];rows=[]
    transfer={'CD_GOTO','CD_GOTO_TRUE','CD_GOTO_FALSE','CD_GOSUB','CD_GOSUBSTR','CD_RETURN','CD_EOF'}
    for i,e in enumerate(tr):
        if e['op'] in transfer:
            if i+1<len(tr):leaders.add(i+1)
            if e.get('target_ofs') in ofs:leaders.add(ofs[e['target_ofs']])
        if e['op']=='CD_TEXT' or (e['op']=='CD_COMMAND' and (e.get('_call_base_name')=='print')):leaders.add(i)
    starts=sorted(leaders);owner={};blocks=[]
    for j,start in enumerate(starts):
        end=starts[j+1] if j+1<len(starts) else len(tr);block_id=variant+':'+scene+':'+str(tr[start]['ofs'])
        blocks.append({'id':block_id,'start':tr[start]['ofs'],'end':tr[end]['ofs'] if end<len(tr) else bundle['header']['scn_size'],'source':str(p),'scene':scene,'variant':variant,'instruction_count':end-start,'ending_opcode':tr[end-1]['op']})
        for i in range(start,end):owner[i]=j
    adjacency=[[] for _ in blocks]
    for j,start in enumerate(starts):
        end=starts[j+1] if j+1<len(starts) else len(tr);e=tr[end-1];op=e['op'];targets=[]
        if op in ('CD_GOTO','CD_GOTO_TRUE','CD_GOTO_FALSE','CD_GOSUB','CD_GOSUBSTR'):
            target=e.get('target_ofs')
            if target in ofs:targets.append((owner[ofs[target]],'call' if 'GOSUB' in op else 'branch' if op!='CD_GOTO' else 'goto'))
            else:unresolved.append({'offset':e['ofs'],'kind':'unresolved-local-target','op':op,'target':target})
        if j+1<len(blocks) and op not in ('CD_GOTO','CD_RETURN','CD_EOF'):
            targets.append((j+1,'continuation' if 'GOSUB' in op else 'fallthrough'))
        for k,kind in targets:
            edges.append({'from':blocks[j]['id'],'to':blocks[k]['id'],'kind':kind,'opcode':op,'condition_status':'bytecode-expression-not-evaluated' if op in ('CD_GOTO_TRUE','CD_GOTO_FALSE') else None});adjacency[j].append((k,kind))
    # Pending explicit names are consumed by the next message. Conflicting incoming states stay unresolved.
    states=[set() for _ in blocks];states[0].add(None);queue=collections.deque([0]);pending_set=[None]*len(tr)
    while queue:
        j=queue.popleft();state=set(states[j]);start=starts[j];end=starts[j+1] if j+1<len(starts) else len(tr)
        for i in range(start,end):
            e=tr[i];op=e['op'];name=e.get('_call_base_name')
            if op=='CD_NAME':state={(e.get('str_id'),e.get('text'))}
            elif op=='CD_COMMAND' and name=='set_namae':
                args=e.get('_arg_values') or [];state={(None,args[0])} if args and isinstance(args[0],str) else {('unknown',None)}
            elif op=='CD_TEXT' or (op=='CD_COMMAND' and name=='print'):
                pending_set[i]=set(state);state={None}
            elif op in ('CD_GOSUB','CD_GOSUBSTR') or (op=='CD_COMMAND' and name in ('farcall','farjump','goto','gosub')):state={('unknown',None)}
        for k,kind in adjacency[j]:
            incoming={('unknown',None)} if kind in ('call','continuation') else state
            new=states[k]|incoming
            if new!=states[k]:states[k]=new;queue.append(k)
    for i,e in enumerate(tr):
        op=e['op'];name=e.get('_call_base_name');args=e.get('_arg_values') or []
        if op=='CD_TEXT' or (op=='CD_COMMAND' and name=='print'):
            text=e.get('text') if op=='CD_TEXT' else args[0] if args and isinstance(args[0],str) else None
            if text is None:unresolved.append({'offset':e['ofs'],'kind':'dynamic-message'});continue
            state=pending_set[i] or set();explicit=[x for x in state if x and x[0]!='unknown' and x[1]]
            speaker=explicit[0][1] if len(state)==1 and len(explicit)==1 else None
            rows.append({'source':str(p),'variant':variant,'scene':scene,'text':text,'speaker':speaker,
                         'speaker_status':'explicit-name-on-all-static-predecessors' if speaker else 'no-pending-name' if state=={None} else 'ambiguous-or-unreachable',
                         'string_index':e.get('str_id'),'code_offset':e['ofs'],'code_base':bundle['header']['scn_ofs'],'source_line':e.get('line'),'read_flag':e.get('read_flag'),
                         'block_id':blocks[owner[i]]['id'],'kind':'message'})
        if op=='CD_COMMAND' and name in ('farcall','farjump','jump','goto','gosub'):
            target=args[0] if args and isinstance(args[0],str) else None
            edges.append({'from':blocks[owner[i]]['id'],'to_scene':target,'entry':args[1] if len(args)>1 else None,'kind':name,'call_offset':e['ofs'],'arguments':args})
            if target is None:unresolved.append({'offset':e['ofs'],'kind':'dynamic-scene-target','command':name})
    return rows,blocks,edges,{'source':str(p),'scene':scene,'variant':variant,'passed':True,'instructions':len(tr),'bytecode_complete':True,'unresolved':unresolved},bundle


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--const-profile',type=int,default=0)
    a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    sys.path.insert(0,str(SSSU));from siglus_ssu import const as C
    C.set_profile(a.const_profile)
    rows,nodes,edges,checks,_=parse_scene(a.input,a.input.stem)
    result={'source_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'dialogue':rows,'flow':{'nodes':nodes,'edges':edges},'checks':checks,'const_profile':a.const_profile,'runtime_verified':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'dialogue':len(rows),'named':sum(bool(r['speaker']) for r in rows),'flow_nodes':len(nodes)}))
if __name__=='__main__':main()
