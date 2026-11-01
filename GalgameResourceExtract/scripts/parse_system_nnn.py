"""Read System-NNN release SPT messages at their instruction positions. No execution."""
# Format reading adapted from VNTranslationTools v0.0.41 (arcusmaximus, MIT).
# License: ../provenance/VNTranslationTools-LICENSE.txt
import json,re,struct
def u32(b,p):
    if not 0 <= p <= len(b)-4: raise ValueError('u32 outside file')
    return struct.unpack_from('<I',b,p)[0]

def systemnnn(p,encoding='cp932'):
    b=bytes(x^255 for x in p.read_bytes());rows=[];nodes=[];i=0
    if len(b)%4 or u32(b,4)!=0x66660001 or u32(b,8)!=0x55550001:raise ValueError('SPT header')
    mc,mt,sc,st=(u32(b,k*4) for k in (4,5,6,7))
    if (mt+mc)*4>len(b) or (st+sc)*4>len(b):raise ValueError('SPT table bounds')
    def getstr(table,count,idx):
        if idx>=count:raise ValueError('SPT string index')
        off=u32(b,4*(table+idx))*4
        if off>=len(b):raise ValueError('SPT string offset')
        end=b.find(b'\0',off)
        if end<off:raise ValueError('SPT missing terminator')
        return b[off:end].decode(encoding),off,end-off
    while i<len(b)//4:
        n=u32(b,4*i)
        if n<2 or i+n>len(b)//4:raise ValueError('SPT item boundary')
        ident=u32(b,4*(i+1));code=u32(b,4*(i+2)) if n>=3 else None
        if ident==0x66660006 and code in (0x22220001,0x22220002,0x22220003,0x22220006):
            if n<4:raise ValueError('SPT short message instruction')
            ids=[u32(b,4*(i+3))]
            choice=code==0x22220006
            if choice:
                nc=ids[0]
                if n!=nc+5:nc+=u32(b,4*(i+n-1))
                if nc>n-4:raise ValueError('SPT choice bounds')
                ids=[u32(b,4*(i+4+j)) for j in range(nc)]
            for idx in ids:
                text,off,length=getstr(st if choice else mt,sc if choice else mc,idx)
                text=re.sub(r'(?m)^//[^\r\n]*(?:\r?\n|$)','',text).rstrip('\r\n')
                m=re.fullmatch(r'([^「『（）』」\r\n]+)\r\n([「『（].+[）』」])\s*',text,re.S)
                rows.append({'text':m[2] if m else text,'speaker':m[1] if m else None,'speaker_status':'inline-name' if m else 'no-name-in-record',
                             'kind':'choice' if choice else 'message','instruction_offset':i*4,'string_offset':off,'string_length':length,'message_id':idx,'opcode':code,'encoding':encoding})
        if ident!=0x66660001 or code in (0x55550003,0x55550004):
            nodes.append({'kind':'spt-instruction','instruction_offset':i*4,'word_index':i,'length_words':n,'identify':ident,'opcode':code})
        i+=n
    return rows,nodes,{'bytes':len(b),'fully_walked':True,'message_count':mc,'choice_string_count':sc,'offset_base':'decoded SPT file; XOR does not change length'}


def main():
    import argparse,hashlib
    from pathlib import Path
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--encoding',default='cp932',help='Explicit project text encoding; not auto-detected')
    a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    rows,nodes,checks=systemnnn(a.input,a.encoding)
    for n in nodes:n['runtime_verified']=False
    result={'source_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'dialogue':rows,'static_nodes':nodes,'checks':checks,'runtime_verified':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'dialogue':len(rows),'nodes':len(nodes)}))
if __name__=='__main__':main()
