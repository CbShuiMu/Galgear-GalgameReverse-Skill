"""Non-executing parser for literal Lua AST tables; rejects executable expressions."""
import re,json
TOKEN=re.compile(r'\s+|--[^\n]*|\[(=*)\[[\s\S]*?\]\1\]|"(?:\\.|[^"\\])*"|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*|[{}\[\]=,;+-]')
def parse(text, allow_duplicate_keys=False):
    ts=[];pos=0
    for m in TOKEN.finditer(text):
        if text[pos:m.start()].strip():raise ValueError('unsupported syntax at '+str(pos))
        z=m[0];pos=m.end()
        if not z.isspace() and not z.startswith('--'):ts.append((z,m.start()))
    if text[pos:].strip():raise ValueError('trailing unsupported syntax')
    i=0
    def take(expected=None):
        nonlocal i
        z=ts[i];i+=1
        if expected is not None and z[0]!=expected:raise ValueError('expected '+expected+' at '+str(z[1]))
        return z
    def value():
        nonlocal i
        z,at=take()
        if re.match(r'^\[=*\[',z):
            head=re.match(r'^\[(=*)\[',z)[0]
            content=z[len(head):-len(head)]
            return content[2:] if content.startswith('\r\n') else content[1:] if content.startswith('\n') else content
        if z=='{':
            d={};seq=1
            while ts[i][0]!='}':
                if ts[i][0]=='[':
                    take('[');key=value();take(']');take('=');v=value()
                elif i+1<len(ts) and ts[i+1][0]=='=':
                    key=take()[0];take('=');v=value()
                else:key=seq;seq+=1;v=value()
                if key in d and not allow_duplicate_keys:raise ValueError('duplicate table key')
                d[key]=v
                if ts[i][0] in [',',';']:take()
                elif ts[i][0]!='}':raise ValueError('missing separator')
            take('}');return d
        if z.startswith('"'):
            try:return json.loads(z,strict=False)
            except ValueError:raise ValueError('unsupported Lua string escape at '+str(at))
        if z in ['-','+']:return (-1 if z=='-' else 1)*value()
        if re.fullmatch(r'\d+(?:\.\d+)?',z):return float(z) if '.' in z else int(z)
        if z in ['true','false','nil']:return {'true':True,'false':False,'nil':None}[z]
        raise ValueError('nonliteral value at '+str(at))
    take('ast');take('=');result=value()
    if i<len(ts) and ts[i][0]==';':take()
    if i!=len(ts):raise ValueError('extra statements')
    return result
def flatten(d):
    if isinstance(d,str):return [d]
    if not isinstance(d,dict):return []
    return [x for k,v in d.items() if isinstance(k,int) for x in flatten(v)]
def extract(path,relative,allow_duplicate_keys=False):
    t=path.read_text(encoding='utf-8-sig');root=parse(t,allow_duplicate_keys=allow_duplicate_keys);rows=[];nodes=[]
    for idx,entry in root.get('text',{}).items():
        if not isinstance(entry,dict):continue
        for lang,val in entry.items():
            if lang in ['name','vo']:continue
            if lang=='select' and isinstance(val,dict):
                for choice_lang,options in val.items():
                    if not isinstance(options,dict):continue
                    for option,text in options.items():
                        if isinstance(option,int) and isinstance(text,str):rows.append({'file':relative,'text_table_id':idx,'language_key':choice_lang,'option_index':option,'text':text,'speaker':None,'kind':'literal-ast-choice','runtime_verified':False})
                continue
            parts=flatten(val)
            if parts:
                name=entry.get('name') or {}
                speaker=(name.get(lang) or name.get('name')) if isinstance(name,dict) else None
                rows.append({'file':relative,'text_table_id':idx,'language_key':lang,'text':'\n'.join(parts),'speaker':speaker,'speaker_fields':entry.get('name'),'voice_commands':entry.get('vo'),'raw_text_table':val,'kind':'literal-ast-text-table'})
    for k,v in root.items():
        if isinstance(k,int) and isinstance(v,dict):
            nodes.append({'file':relative,'ast_block':k,'language_reference':v.get('lang'),'kind':'ast-block','runtime_verified':False})
    for key,val in root.get('label',{}).items():nodes.append({'file':relative,'label':key,'target':val,'kind':'ast-label','runtime_verified':False})
    return rows,nodes

def main():
    import argparse, hashlib
    from pathlib import Path
    ap=argparse.ArgumentParser(description="Read literal ast={...} Lua tables without executing code")
    ap.add_argument("input",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("--allow-duplicate-keys",action="store_true",help="Use Lua last-assignment semantics for literal duplicate keys")
    args=ap.parse_args()
    if args.output.exists():ap.error("output already exists")
    rows,nodes=extract(args.input,args.input.name,args.allow_duplicate_keys)
    result={"source_sha256":hashlib.sha256(args.input.read_bytes()).hexdigest(),"dialogue":rows,"static_nodes":nodes,"runtime_verified":False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as out:json.dump(result,out,ensure_ascii=False,indent=2)
    print(json.dumps({"dialogue":len(rows),"static_nodes":len(nodes)}))
if __name__=="__main__":main()
