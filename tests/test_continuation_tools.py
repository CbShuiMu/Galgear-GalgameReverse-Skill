"""Synthetic boundaries for portable readers added during serial refinement."""
import importlib.util,json,pathlib,pickle,shutil,struct,subprocess,sys,tempfile,unittest,zlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
SK=ROOT/'GalgameResourceExtract'
sys.path.insert(0,str(SK/'scripts'))
from passive_pickle import read,Box
from locate_renpy_save import bounded_zlib
from parse_ast_flow import scan
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
Y=module('test_yuris_reader',SK/'tools/yuris-cli/yuris_cli.py')
A=module('test_artemis_reader',SK/'tools/artemis-save/artemis_save_cli.py')

class Readers(unittest.TestCase):
    def test_passive_pickle_reducers_are_data(self):
        value=read(b"cos\nsystem\n(Vnot-a-command\ntR.")
        self.assertIsInstance(value,Box);self.assertEqual(value.kind,'REDUCE')
        self.assertEqual(value.args[0].args,'os system')
        self.assertEqual(read(pickle.dumps({'a':[1,2,3]},protocol=2)),{'a':[1,2,3]})
    def test_legacy_script_digest_and_limit(self):
        self.assertEqual(bounded_zlib(zlib.compress(b'abc')+bytes(16),20),b'abc')
        for data,limit in ((zlib.compress(b'abc')+b'x',20),(zlib.compress(b'abc'),2)):
            with self.assertRaises(ValueError):bounded_zlib(data,limit)
    def test_ypf_checksum_and_unsafe_name(self):
        name=b'a.ybn';body=b'YSTB synthetic';end=32+5+len(name)+18
        data=struct.pack('<4sIII16x',b'YPF\0',474,1,end)+struct.pack('<IB',zlib.crc32(name),len(name)^255)+bytes(x^255 for x in name)+struct.pack('<BBIIII',0,0,len(body),len(body),end,zlib.adler32(body))+body
        entry=Y.ypf_entries(data)[0];self.assertEqual(Y.ypf_payload(data,entry),body)
        with tempfile.TemporaryDirectory() as td:
            dest=pathlib.Path(td)/'installed';shutil.copytree(SK/'tools/yuris-cli',dest)
            inp=pathlib.Path(td)/'test.ypf';out=pathlib.Path(td)/'raw';inp.write_bytes(data)
            p=subprocess.run([sys.executable,str(dest/'yuris_cli.py'),'extract',str(inp),str(out)],cwd=td,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertEqual((out/'a.ybn').read_bytes(),body);self.assertEqual(inp.read_bytes(),data)
        with self.assertRaises(ValueError):Y.ypf_payload(data[:-1]+b'x',entry)
        for name in ('../a','C:/a','/a','a/../b','NUL.txt'):
            with self.assertRaises(ValueError):Y.safe_name(name)
    def test_ystb_word_identity_and_descriptor_bounds(self):
        text='A「Hello」'.encode('cp932');code=struct.pack('<BBHBBH',0,1,0,1,0,0);desc=struct.pack('<HHII',0,0,len(text),0)
        data=struct.pack('<4s7I',b'YSTB',474,2,len(code),len(desc),len(text),8,0)+code+desc+text+struct.pack('<II',12,13)
        r=Y.ystb(data,[{'name':'WORD'},{'name':'RETURN'}]);self.assertEqual(r['dialogue'][0]['speaker'],'A');self.assertEqual(r['dialogue'][0]['text'],'Hello');self.assertEqual(r['instructions'][0]['line'],12)
        with self.assertRaises(ValueError):Y.ystb(data[:-1],[{'name':'WORD'},{'name':'RETURN'}])
    def test_ast_archives_are_not_merged(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            for group in ('base','patch'):
                p=root/group;p.mkdir();(p/'a.ast').write_text('ast={{{"excall",file="b"}}}',encoding='utf-8');(p/'b.ast').write_text('ast={{}}',encoding='utf-8')
            result=scan(root);self.assertEqual(len(result['references']),2)
            for ref in result['references']:
                self.assertEqual(len(ref['scene_candidates']),1);self.assertEqual(pathlib.Path(ref['scene_candidates'][0]).parent,pathlib.Path(ref['source']).parent)
    def test_artemis_cli_runs_from_isolated_install(self):
        fields=bytearray(64);script=b'system/script.asb';struct.pack_into('<I',fields,16,len(script));fields[20:20+len(script)]=script;struct.pack_into('<I',fields,48,7)
        groups={0:{3:8},8:{3:16,4:48}};ref=A.load_reader();body=ref.IndexedSave.make_body(bytes(fields),groups);data=b'BOWS'+struct.pack('<II',1003,len(body))+zlib.compress(body)
        with tempfile.TemporaryDirectory() as td:
            dest=pathlib.Path(td)/'installed';shutil.copytree(SK/'tools/artemis-save',dest)
            inp=pathlib.Path(td)/'synthetic.dat';out=pathlib.Path(td)/'result.json';inp.write_bytes(data)
            p=subprocess.run([sys.executable,str(dest/'artemis_save_cli.py'),str(inp),str(out)],cwd=td,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr);r=json.loads(out.read_text('utf-8'));self.assertEqual(r['active_caret']['command_index'],7);self.assertEqual(inp.read_bytes(),data)
            with self.assertRaises(ValueError):A.inspect(data[:-1])
if __name__=='__main__':unittest.main()
