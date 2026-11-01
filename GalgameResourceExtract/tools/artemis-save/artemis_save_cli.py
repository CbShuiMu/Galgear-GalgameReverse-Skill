"""Read Artemis BOW* indexed save containers. Never modifies a save or runs Lua."""
import argparse,hashlib,importlib.util,json,struct,sys,zlib
from pathlib import Path

def load_reader():
    spec=importlib.util.spec_from_file_location('artemis_save_reference',Path(__file__).parent/'source/artemis-save.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def inspect(data,max_bytes=64*1024*1024):
    if len(data)<16:raise ValueError('truncated header')
    magic,version,size=struct.unpack_from('<4sII',data)
    if magic not in (b'BOWS',b'BOWG',b'BOWX') or version not in (1002,1003):raise ValueError('unsupported container')
    if size>max_bytes:raise ValueError('expanded body exceeds limit')
    obj=zlib.decompressobj();body=obj.decompress(data[12:],size+1)
    if len(body)!=size or not obj.eof or obj.unused_data or obj.unconsumed_tail:raise ValueError('compressed size or boundary mismatch')
    save=load_reader().IndexedSave(data)
    for base,entries in save.groups.items():
        if not 0<=base<save.index_start:raise ValueError('object base outside fields')
        if any(not base<=offset<save.index_start for offset in entries.values()):raise ValueError('field pointer outside object/body')
    result={'source_sha256':hashlib.sha256(data).hexdigest(),'magic':magic.decode(),'version':version,'body_size':size,'object_count':len(save.groups),'index_roundtrip':True,'runtime_verified':False,'story_position_verified':False}
    root=save.groups[0]
    if 3 in root and root[3] in save.groups:
        caret=save.groups[root[3]]
        if all(k in caret for k in (3,4)):
            script=save.lp(caret[3]).decode('utf-8')
            result['active_caret']={'object_offset':root[3],'script_field_offset':caret[3],'script':script,'command_field_offset':caret[4],'command_index':save.num(caret[4]),'scope':'engine ASB caret; AST story position requires game macro state'}
    result['status']='active-engine-caret-decoded' if 'active_caret' in result else 'indexed-container-only'
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--max-bytes',type=int,default=64*1024*1024);a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    try:r=inspect(a.input.read_bytes(),a.max_bytes)
    except (ValueError,KeyError,struct.error,zlib.error,UnicodeError) as ex:ap.exit(1,str(ex)+'\n')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':r['status'],'objects':r['object_count']}))
if __name__=='__main__':main()
