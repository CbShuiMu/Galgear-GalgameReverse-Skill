"""Inspect legacy Ren'Py (roots, RollbackLog) saves and match native AST names.

Uses pickletools with inert object graphs; never imports pickle globals, calls
reducers, executes script Python or starts Ren'Py. RPYC2 and modern save schemas
are outside this reader's scope. A matched AST coordinate is not a load test.
"""
import argparse,hashlib,json,zipfile,zlib
from pathlib import Path
from passive_pickle import Box,read,walk

def fields(obj):
    if not isinstance(obj,Box):return {}
    state=obj.state
    if isinstance(state,dict):return state
    if isinstance(state,tuple) and len(state)==2:
        result={}
        for part in state:
            if isinstance(part,dict):result.update(part)
        return result
    return {}

def class_name(obj):
    if isinstance(obj,Box) and obj.kind=='NEWOBJ' and isinstance(obj.args[0],Box) and obj.args[0].kind=='GLOBAL':return obj.args[0].args
    return None

def bounded_zlib(data,limit):
    obj=zlib.decompressobj();raw=obj.decompress(data,limit+1)
    # Legacy RPYC optionally appends a 16-byte source digest after zlib.
    if len(raw)>limit or not obj.eof or len(obj.unused_data) not in (0,16) or obj.unconsumed_tail:raise ValueError('unsupported compressed script size/boundary')
    return raw

def locate(save_path,script_root,max_bytes=64*1024*1024):
    with zipfile.ZipFile(save_path) as z:
        if z.namelist().count('log')!=1:raise ValueError('save log member missing or duplicate')
        if z.getinfo('log').file_size>max_bytes:raise ValueError('save log size limit')
        root=read(z.read('log'))
    if not isinstance(root,tuple) or len(root)!=2 or class_name(root[1]) not in ('renpy.python RollbackLog','renpy.rollback RollbackLog'):raise ValueError('unsupported save root schema')
    log=fields(root[1]);current=fields(log.get('current'));context=current.get('context')
    if class_name(context)!='renpy.execution Context':raise ValueError('active rollback context not found')
    state=fields(context);native=state.get('current')
    if not isinstance(native,(str,tuple)):raise ValueError('unsupported native node identity')
    matches=[];checks=[]
    for p in sorted(script_root.rglob('*.rpyc')):
        try:
            data=p.read_bytes();ast=read(bounded_zlib(data,max_bytes));found=0
            for _,node in walk(ast):
                f=fields(node)
                if f.get('name')!=native:continue
                found+=1;matches.append({'source':str(p),'sha256':hashlib.sha256(data).hexdigest(),'node_class':class_name(node),'name':f.get('name'),'filename':f.get('filename'),'line':f.get('linenumber'),'speaker_id':f.get('who'),'text':f.get('what')})
            checks.append({'source':str(p),'passed':True,'matches':found})
        except (ValueError,KeyError,IndexError,TypeError,zlib.error,UnicodeError) as ex:checks.append({'source':str(p),'passed':False,'error':str(ex)})
    last_say=root[0].get('_last_say_what') if isinstance(root[0],dict) else None
    for m in matches:m['saved_last_say_matches']=isinstance(last_say,str) and m['text']==last_say
    return {'source':str(save_path),'sha256':hashlib.sha256(save_path.read_bytes()).hexdigest(),'active_native_node':native,'return_stack':state.get('return_stack'),'rollback_history_count':len(log.get('log',[])),
        'matches':matches,'script_checks':checks,'active_field_decoded':True,'static_coordinate_matches':len(matches),'position_status':'native-node-match' if len(matches)==1 else 'ambiguous-native-node-match' if matches else 'active-node-not-found-in-supplied-scripts','runtime_verified':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('scripts',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    r=locate(a.input,a.scripts);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print(json.dumps({'position_status':r['position_status'],'matches':len(r['matches']),'history':r['rollback_history_count']}))
if __name__=='__main__':main()
