"""Read-only YPF 474 and YSTB 474 CLI, with explicit bounds and checksum checks.

YPF reader adapted from morkt/GARbro ArcYPF.cs (MIT).
YSCM/YSTB layout and WORD consumer follow VNTranslationTools v0.0.41 (MIT).
Corresponding reference source, licenses and pinned revisions accompany this file.
"""
import argparse,hashlib,json,re,struct,zlib
from pathlib import Path,PurePosixPath

def sha(b):return hashlib.sha256(b).hexdigest()
def safe_name(name):
    name=name.replace('\\','/');p=PurePosixPath(name)
    if not name or p.is_absolute() or ':' in name or any(x in ('..','') for x in name.split('/')):raise ValueError('unsafe member path')
    if any(x.endswith((' ','.')) or x.split('.')[0].upper() in ('CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]) for x in p.parts):raise ValueError('unsafe Windows member name')
    return name

def ypf_entries(data):
    if len(data)<32:raise ValueError('truncated YPF header')
    magic,version,count,end=struct.unpack_from('<4sIII',data)
    if magic!=b'YPF\0' or version!=474:raise ValueError('only YPF 474 is supported')
    if not 32<=end<=len(data) or not 0<count<=100000 or count>(end-32)//23:raise ValueError('YPF index bounds')
    swap=list(range(256))
    for a,b in ((3,72),(6,53),(12,16),(17,25),(28,30),(9,11),(13,19),(21,27),(32,35),(38,41),(44,47),(46,50)):swap[a],swap[b]=swap[b],swap[a]
    cursor=32;entries=[];names=set()
    for _ in range(count):
        if cursor+5>end:raise ValueError('truncated YPF name header')
        namehash,length=struct.unpack_from('<IB',data,cursor);cursor+=5;length=swap[length^255]
        if not length or cursor+length+18>end:raise ValueError('YPF index entry bounds')
        encoded=bytes(x^255 for x in data[cursor:cursor+length]);cursor+=length
        if zlib.crc32(encoded)!=namehash:raise ValueError('YPF name checksum mismatch; unsupported name encoding/key')
        name=safe_name(encoded.decode('cp932'))
        if name.casefold() in names:raise ValueError('duplicate member path')
        names.add(name.casefold())
        kind,packed,size,compressed,offset,checksum=struct.unpack_from('<BBIIII',data,cursor);cursor+=18
        if packed not in (0,1) or offset<end or offset+compressed>len(data):raise ValueError('YPF payload bounds or compression flag')
        entries.append(dict(name=name,kind=kind,packed=packed,size=size,compressed=compressed,offset=offset,checksum=checksum))
    if cursor!=end:raise ValueError('YPF index trailing bytes')
    return entries

def ypf_payload(data,entry,max_bytes=64*1024*1024):
    if entry['size']>max_bytes:raise ValueError('member expanded size limit')
    raw=data[entry['offset']:entry['offset']+entry['compressed']]
    if zlib.adler32(raw)!=entry['checksum']:raise ValueError('YPF member checksum mismatch')
    if entry['packed']:
        obj=zlib.decompressobj();raw=obj.decompress(raw,entry['size']+1)
        if not obj.eof or obj.unused_data or obj.unconsumed_tail:raise ValueError('YPF compressed boundary mismatch')
    if len(raw)!=entry['size']:raise ValueError('YPF member size mismatch')
    return raw

def command_list(data):
    if len(data)<16 or data[:4]!=b'YSCM':raise ValueError('YSCM header')
    version,count=struct.unpack_from('<II',data,4)
    if version!=474 or not 0<count<256:raise ValueError('YSCM version/count')
    cursor=16;commands=[]
    def string():
        nonlocal cursor
        end=data.index(b'\0',cursor);value=data[cursor:end].decode('cp932');cursor=end+1;return value
    for _ in range(count):
        name=string();num=data[cursor];cursor+=1;attrs=[]
        for _ in range(num):
            attrs.append(string());cursor+=2
            if cursor>len(data):raise ValueError('YSCM attribute boundary')
        commands.append(dict(name=name,attributes=attrs))
    # Releases may append engine diagnostics after the declared command table.
    # They are not command definitions; preserve the original file as evidence.
    return commands

def decode_word(raw,encoding):
    raw=bytearray(raw);i=0
    while i+1<len(raw):
        if raw[i]==0xef:
            pair={0xf0:b'\r\n',0xf2:b'\\p',0xf3:b'\\c',0xf5:b'\\u'}.get(raw[i+1])
            if pair:raw[i:i+2]=pair
            i+=2
        else:i+=2 if 0x81<=raw[i]<=0x9f or 0xe0<=raw[i]<=0xfc else 1
    return bytes(raw).decode(encoding)

def ystb(data,commands,encoding='cp932'):
    if len(data)<32:raise ValueError('YSTB truncated header')
    magic,version,count,code_size,desc_size,value_size,line_size,_=struct.unpack_from('<4s7I',data)
    if magic!=b'YSTB' or version!=474 or code_size!=count*4 or desc_size%12 or line_size!=count*4:raise ValueError('YSTB version/section sizes')
    if 32+code_size+desc_size+value_size+line_size!=len(data):raise ValueError('YSTB file bounds')
    base=32+code_size+desc_size
    if desc_size<12:raise ValueError('YSTB key probe unavailable')
    # The reference infers the XOR word from the first attribute value offset (zero).
    # Every descriptor and operand boundary below must validate after this inference.
    key=data[32+code_size+8:32+code_size+12];decoded=bytearray(data);cursor=32
    for length in (code_size,desc_size,value_size,line_size):
        for i in range(length):decoded[cursor+i]^=key[i%4]
        cursor+=length
    values=decoded[base:base+value_size];dc=32+code_size;trace=[];rows=[];pending=[];spans=[];unresolved=[]
    def flush():
        if pending:
            text=''.join(pending);m=re.fullmatch(r'(.+?)(?:[「『](.+)[』」]|(（.+）))',text,re.S)
            rows.append({'text':(m[2] or m[3]) if m else text,'speaker':m[1] if m else None,'speaker_status':'inline-WORD-group-name' if m else 'no-inline-name','instruction_offsets':spans.copy(),'kind':'WORD-message','runtime_verified':False})
        pending.clear();spans.clear()
    for i in range(count):
        off=32+i*4;op,argc,npar=struct.unpack_from('<BBH',decoded,off)
        if op>=len(commands):raise ValueError('unknown YSTB command')
        name=commands[op]['name'];attrs=[]
        for arg_index in range(argc):
            if dc+12>base:raise ValueError('YSTB descriptor overrun')
            aid,typ,size,at=struct.unpack_from('<HHII',decoded,dc)
            # IF/ELSE/LOOP carry control metadata after the first expression;
            # those integers are not offsets into the value section.
            metadata=(name in ('IF','ELSE') and argc==3 and arg_index>0) or (name=='LOOP' and argc==2 and arg_index==1) or name=='RETURNCODE'
            if not metadata and at+size>len(values):raise ValueError('YSTB value bounds')
            attrs.append({'id':aid,'type':typ,'size':size,'offset':None if metadata else base+at,'stored_offset':at,'descriptor_offset':dc,'control_metadata':metadata,'raw_hex':None if metadata else bytes(values[at:at+size]).hex()});dc+=12
        source_line=struct.unpack_from('<I',decoded,base+value_size+i*4)[0]
        if name=='WORD' and attrs and attrs[0]['type']==0:
            a=attrs[0];text=decode_word(bytes.fromhex(a['raw_hex']),encoding);a['literal_text']=text;pending.append(text);spans.append(off)
        else:
            flush()
            if name in ('WORD','EVAL','GOSUB'):unresolved.append({'offset':off,'command':name,'status':'dynamic-or-additional-consumer-not-classified'})
        trace.append({'offset':off,'code_offset':i*4,'line':source_line,'command':name,'opcode':op,'parameter_count':npar,'attributes':attrs})
    flush()
    if dc!=base:raise ValueError('unused YSTB descriptors')
    return {'source_sha256':sha(data),'dialogue':rows,'instructions':trace,'unresolved':unresolved,'complete_instruction_walk':True,'story_complete':False,'runtime_verified':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='mode',required=True)
    for name in ('list','extract','script'):
        p=sub.add_parser(name);p.add_argument('input',type=Path);p.add_argument('output',type=Path)
        if name=='script':p.add_argument('--commands',type=Path,required=True);p.add_argument('--encoding',default='cp932')
    a=ap.parse_args()
    if a.output.exists():ap.error('output already exists')
    data=a.input.read_bytes()
    if a.mode=='script':result=ystb(data,command_list(a.commands.read_bytes()),a.encoding)
    else:
        entries=ypf_entries(data);result={'source_sha256':sha(data),'version':474,'entries':entries,'raw_payloads':True}
        if a.mode=='extract':
            # Validate every payload before creating the output directory.
            for e in entries:ypf_payload(data,e)
            a.output.mkdir(parents=True)
            for e in entries:
                p=a.output/e['name'];p.parent.mkdir(parents=True,exist_ok=True);raw=ypf_payload(data,e);p.write_bytes(raw);e['sha256']=sha(raw)
            a.output=a.output/'extraction-manifest.json'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'mode':a.mode,'entries':len(result.get('entries',[])),'messages':len(result.get('dialogue',[]))}))
if __name__=='__main__':main()
