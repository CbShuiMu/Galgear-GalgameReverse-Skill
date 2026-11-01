"""Installed parser boundary checks, with synthetic inputs only."""
import importlib.util
from pathlib import Path
import struct,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'GalgameResourceExtract/scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
AST=load('gal_literal_ast','parse_ast_tables.py')
SPT=load('gal_release_spt','parse_system_nnn.py')
MJO=load('gal_majiro_v1','parse_majiro_v1.py')
SIG=load('gal_siglus_flow','parse_siglus_flow.py')

class ScriptParsers(unittest.TestCase):
    def test_majiro_assembly_and_branch_name_boundary(self):
        def instruction(off,name,args=(),targets=()):
            return dict(offset=off,end=off+2,name=name,operands=list(args),targets=list(targets))
        trace=[instruction(0,'text',['A「hel']),instruction(2,'proc'),
               instruction(4,'text',['lo」']),instruction(6,'ctrl',['p']),
               instruction(8,'text',['Narration']),instruction(10,'br',[0],[14]),
               instruction(12,'text',['B「']),instruction(14,'text',['Other branch']),
               instruction(16,'ret'),instruction(18,'ldstr',['Choice A']),
               instruction(20,'ldstr',['Choice B']),instruction(22,'callp',[0x0A7A489C,0,2])]
        messages,choices,_=MJO.assemble_messages(trace)
        self.assertEqual(messages[0]['text'],'「hello」')
        self.assertEqual(messages[0]['speaker'],'A')
        self.assertIsNone(messages[1]['speaker'])
        self.assertIsNone(messages[3]['speaker'])
        self.assertEqual([r['text'] for r in choices],['Choice A','Choice B'])
        self.assertEqual(messages[0]['instruction_offsets'],[0,4])
    def test_majiro_native_fragment_and_bad_length(self):
        text='A「hello」'.encode('cp932')+b'\0';code=struct.pack('<HH',0x840,len(text))+text+struct.pack('<HH',0x841,0x82b)
        header=b'MajiroObjV1.000\0'+struct.pack('<6I',0,0,1,123,0,len(code))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'s.mjo';p.write_bytes(header+code)
            rows,_,_,checks=MJO.read_majiro(p,ROOT/'GalgameResourceExtract/assets/majiro-v1-opcodes.json')
            self.assertEqual(rows[0]['speaker'],'A');self.assertEqual(checks['code_base'],40)
            p.write_bytes((header+code)[:-1])
            with self.assertRaises(ValueError):MJO.read_majiro(p,ROOT/'GalgameResourceExtract/assets/majiro-v1-opcodes.json')
    def test_siglus_pending_name_consumed_and_no_branch_guess(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0,str(SIG.SSSU));from siglus_ssu import dat
        trace=[{'op':'CD_NAME','ofs':0,'str_id':0,'text':'A'},{'op':'CD_TEXT','ofs':10,'str_id':1,'text':'Hello'},{'op':'CD_TEXT','ofs':20,'str_id':2,'text':'Narration'},{'op':'CD_EOF','ofs':30}]
        bundle={'complete':True,'trace':trace,'header':{'scn_size':60,'scn_ofs':132}}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'s.dat';p.write_bytes(b'synthetic')
            with patch.object(dat,'dat_disassembly_bundle',return_value=bundle):
                rows,_,_,_,_=SIG.parse_scene(p,'s');self.assertEqual([r['speaker'] for r in rows],['A',None])
    def test_ast_long_string_duplicate_and_no_execution(self):
        self.assertEqual(AST.parse('ast={x=[=[a"b\n]=]}')['x'],'a"b\n')
        self.assertEqual(AST.parse('ast={x=1,x=2}',True)['x'],2)
        self.assertEqual(AST.parse('ast={x="a\tb"}')['x'],'a\tb')
        for t in ('ast={x=1,x=2}','ast={x=os.execute("x")}','ast={x=[=[oops}'):
            with self.assertRaises((ValueError,IndexError)):AST.parse(t)
    def test_ast_nested_selection_languages(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'s.ast';p.write_text('ast={text={[1]={select={ja={"A","B"}}}}}',encoding='utf-8')
            rows,_=AST.extract(p,p.name)
            self.assertEqual([r['text'] for r in rows],['A','B']);self.assertEqual(rows[0]['kind'],'literal-ast-choice')
    def test_spt_word_units_and_invalid_boundaries(self):
        raw='名字\r\n「你好」'.encode('gbk')+b'\0';raw+=bytes((-len(raw))%4)
        h=[16,0x66660001,0x55550001,0,1,8,0,0,24]+[0]*7
        msg=[4,0x66660006,0x22220001,0]
        data=[4+len(raw)//4,0x66660001,0x55550002,0x44440002]
        b=struct.pack('<24I',*(h+msg+data))+raw
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'synthetic.spt'
            def put(v):p.write_bytes(bytes(x^255 for x in v))
            put(b);rows,_,check=SPT.systemnnn(p,'gbk')
            self.assertEqual(rows[0]['speaker'],'名字');self.assertEqual(rows[0]['instruction_offset'],64)
            self.assertEqual(rows[0]['string_offset'],96);self.assertTrue(check['fully_walked'])
            for offset,value in ((64,0),(32,0xffffffff),(20,0xffffffff)):
                c=bytearray(b);struct.pack_into('<I',c,offset,value);put(c)
                with self.assertRaises(ValueError):SPT.systemnnn(p,'gbk')
            put(b[:-1])
            with self.assertRaises(ValueError):SPT.systemnnn(p,'gbk')
if __name__=='__main__':unittest.main()
