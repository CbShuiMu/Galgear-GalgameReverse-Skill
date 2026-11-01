"""Read Majiro V1 code, message fragments and local branch references. No execution.
Format/opcode reference: VNTranslationTools v0.0.41 (MIT).
See provenance/VNTranslationTools-LICENSE.txt.
"""
import re,struct,json,hashlib
from pathlib import Path

def u32(b,p):
    if not 0<=p<=len(b)-4:raise ValueError('u32 outside input')
    return struct.unpack_from('<I',b,p)[0]

def read_majiro(p,opcode_source,encoding='cp932'):
    templates={int(k):tuple(v) for k,v in json.loads(opcode_source.read_text(encoding='utf-8'))['templates'].items()}
    raw=p.read_bytes();sig=raw[:16]
    if sig not in (b'MajiroObjV1.000\0',b'MajiroObjX1.000\0'):raise ValueError('MJO V1 header mismatch')
    n=u32(raw,24);base=32+n*8
    if n>100000 or base>len(raw) or base+u32(raw,base-4)!=len(raw):raise ValueError('MJO code/function bounds')
    code=raw[base:];functions=[u32(raw,32+i*8) for i in range(n)]
    if sig[9:10]==b'X':
        table=[]
        for x in range(256):
            for _ in range(8):x=(x>>1)^0xedb88320 if x&1 else x>>1
            table.extend(struct.pack('<I',x))
        code=bytes(v^table[i%1024] for i,v in enumerate(code))
    pos=0;tr=[];rows=[];candidates=[]
    def take(fmt):
        nonlocal pos
        size=struct.calcsize(fmt)
        if pos+size>len(code):raise ValueError('truncated MJO operand')
        v=struct.unpack_from(fmt,code,pos)[0];pos+=size;return v
    while pos<len(code):
        off=pos;op=take('<H')
        if op not in templates:raise ValueError('unknown MJO opcode '+hex(op)+' at '+hex(off))
        template,name=templates[op];args=[];targets=[];str_offsets=[]
        for t in template:
            if t=='s':
                length=take('<H');so=pos
                if length and (pos+length>len(code) or code[pos+length-1]!=0):raise ValueError('MJO string boundary')
                value=code[pos:pos+max(0,length-1)].decode(encoding);pos+=length;args.append(value);str_offsets.append(so)
            elif t in 'ti':
                if t=='i':args.append(take('<i'))
                else:
                    count=take('<H')
                    if pos+count>len(code):raise ValueError('MJO type list')
                    args.extend(code[pos:pos+count]);pos+=count
            elif t in 'fh0oarlj':
                if t=='j':
                    distance=take('<i');args.append(distance);targets.append(pos+distance)
                else:args.append(take({'f':'<H','h':'<i','0':'<i','o':'<h','a':'<H','r':'<f','l':'<H'}[t]))
            elif t=='c':
                count=take('<H')
                if pos+4*count>len(code):raise ValueError('MJO switch boundary')
                for _ in range(count):distance=take('<i');args.append(distance);targets.append(pos+distance)
            else:raise ValueError('unknown operand template')
        tr.append({'offset':off,'end':pos,'opcode':op,'name':name.strip(),'targets':targets,'operands':args})
        if op in (0x840,0x801):
            text=args[0];m=re.match(r'^([^「」\r\n]{1,40})「(.*)',text,re.S)
            rec={'source':str(p),'text':text if not m else '「'+m[2],'raw_fragment':text,'speaker':m[1] if m and op==0x840 else None,'speaker_status':'inline-fragment-name' if m and op==0x840 else 'no-name-in-fragment','code_offset':off,'code_base':base,'string_offset':base+str_offsets[0],'kind':'message-fragment' if op==0x840 else 'ldstr-candidate','scene':p.stem}
            (rows if op==0x840 else candidates).append(rec)
    boundaries={v['offset'] for v in tr}
    invalid=[t for v in tr for t in v['targets'] if t not in boundaries]
    if invalid:raise ValueError('MJO targets not at instruction boundaries')
    if any(x not in boundaries for x in functions):raise ValueError('MJO function entry boundary')
    return rows,candidates,tr,{'code_base':base,'code_size':len(code),'instructions':len(tr),'functions':functions,'complete':pos==len(code)}

def binary_graph(p,tr,scene,base,functions=()):
    byoff={v['offset']:i for i,v in enumerate(tr)};leaders={0}|{byoff[x] for x in functions};nodes=[];edges=[]
    for i,v in enumerate(tr):
        if v['targets'] or v['name'] in ('ret','call','callp','text','switch'):
            leaders.add(i)
            if i+1<len(tr):leaders.add(i+1)
        for target in v['targets']:leaders.add(byoff[target])
    starts=sorted(leaders);owner={}
    for j,start in enumerate(starts):
        end=starts[j+1] if j+1<len(starts) else len(tr);v=tr[start]
        node={'id':str(p)+':'+str(v['offset']),'source':str(p),'scene':scene,'code_base':base,'start':v['offset'],'end':tr[end-1]['end'],'ending_opcode':tr[end-1]['name']};nodes.append(node)
        for i in range(start,end):owner[i]=j
    for j,start in enumerate(starts):
        end=starts[j+1] if j+1<len(starts) else len(tr);v=tr[end-1]
        for target in v['targets']:edges.append({'from':nodes[j]['id'],'to':nodes[owner[byoff[target]]]['id'],'kind':'bytecode-branch','opcode':v['name'],'condition_evaluated':False})
        if j+1<len(nodes) and v['name'] not in ('br','ret'):
            edges.append({'from':nodes[j]['id'],'to':nodes[j+1]['id'],'kind':'call-continuation' if v['name'] in ('call','callp') else 'fallthrough'})
    return nodes,edges


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--encoding',default='cp932')
    a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    templates=Path(__file__).resolve().parents[1]/'assets/majiro-v1-opcodes.json'
    rows,candidates,trace,checks=read_majiro(a.input,templates,a.encoding)
    nodes,edges=binary_graph(a.input,trace,a.input.stem,checks['code_base'],checks['functions'])
    result={'source_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'message_fragments':rows,'string_candidates':candidates,'flow':{'nodes':nodes,'edges':edges},'checks':checks,'runtime_verified':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'message_fragments':len(rows),'string_candidates':len(candidates),'flow_nodes':len(nodes)}))
if __name__=='__main__':main()
