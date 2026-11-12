"""Installed parser boundary checks, with synthetic inputs only."""
import importlib.util
from pathlib import Path
import struct,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'GalgameResourceExtract/scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
AST=load('gal_literal_ast','parse_ast_tables.py')
SPT=load('gal_release_spt','parse_system_nnn.py')
MJO=load('gal_majiro_v1','parse_majiro_v1.py')
SIG=load('gal_siglus_flow','parse_siglus_flow.py')
SC=load('gal_musica_sc','parse_musica_sc.py')
with patch.object(sys, "path", [str(ROOT / "GalgameResourceExtract/scripts"), *sys.path]):
    SC_TRACE = load("gal_musica_trace", "trace_musica_sc.py")
    MJO_FLOW = load("gal_majiro_flow", "index_majiro_flow.py")
    MJO_SAVE = load("gal_majiro_save", "locate_majiro_save.py")

class ScriptParsers(unittest.TestCase):
    def test_musica_include_resumes_in_caller_and_keeps_overlay_coordinates(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "base"
            overlay = Path(td) / "overlay"
            base.mkdir()
            overlay.mkdir()
            (base / "start.sc").write_bytes(
                b".if seen == 1 repeat\n#include Part.sc\n.label repeat\n.message 10   Tail\n.end\n"
            )
            (base / "part.sc").write_bytes(b".message 10   Original\n")
            (overlay / "part.sc").write_bytes(b".message 10   Overlay\n")
            scripts, origins = SC_TRACE.load_layers(base, overlay)
            trace = SC_TRACE.trace(scripts, origins, "start.sc", {"seen": 0})
            self.assertEqual([m["text"] for m in trace["messages"]], ["Overlay", "Tail"])
            self.assertEqual([m["group"] for m in trace["messages"]], ["overlay", "base"])
            self.assertEqual(trace["control"][1]["target"]["byte_offset"], 0)
            self.assertEqual(trace["termination"], "end")
            repeat = SC_TRACE.trace(scripts, origins, "start.sc", {"seen": 1})
            self.assertEqual([m["text"] for m in repeat["messages"]], ["Tail"])
            with self.assertRaisesRegex(ValueError, "missing initial value"):
                SC_TRACE.trace(scripts, origins, "start.sc", {})

            report = SC.extract(base, "cp932", "cp932")
            include = next(ref for ref in report["control_flow"] if ref["command"] == "include")
            self.assertEqual(include["continuation"]["line"], 3)
            (base / "bad.sc").write_bytes(b"#include\n.end\n")
            with self.assertRaisesRegex(ValueError, "bad.sc:1: malformed #include"):
                SC.extract(base, "cp932", "cp932")

    def test_majiro_script_transfer_and_alternate_pc_coordinates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def make_mjo(path, code, function_hash=123):
                path.write_bytes(b"MajiroObjV1.000\0" + struct.pack("<6I", 0, 0, 1, function_hash, 0, len(code)) + code)

            target_name = "試験"
            target_arg = (target_name + ".txt").encode("cp932") + b"\0"
            code = struct.pack("<HH", 0x801, len(target_arg)) + target_arg
            code += struct.pack("<HIH", 0x835, 0x718EF651, 1)
            code += struct.pack("<HiHHH", 0x83B, 4, 0x83A, 15, 0x82B)
            make_mjo(root / "start.mjo", code)
            make_mjo(root / (target_name + ".mjo"), struct.pack("<H", 0x82B), 124)
            strict = MJO_FLOW.index([("base", root, "cp932", None)])
            start = next(s for s in strict["scripts"] if s["file"] == "start.mjo")
            self.assertEqual(start["script_transfers"][0]["status"], "missing-script")
            result = MJO_FLOW.index([("base", root, "cp932", None)], strip_script_suffix=True)
            start = next(s for s in result["scripts"] if s["file"] == "start.mjo")
            ref = start["script_transfers"][0]
            self.assertEqual((ref["status"], ref["target_key"], ref["target"]["file_offset"]),
                             ("resolved", target_name + ".mjo", 40))
            self.assertEqual(start["functions"][0]["hash"], 123)
            branch = start["branches"][0]
            self.assertEqual(branch["kind"], "alternate-pc-registration")
            self.assertEqual(branch["targets"][0]["code_offset"], branch["next"]["code_offset"] + 4)

    def test_majiro_menu_reports_numeric_cases_without_guessing_ordinal(self):
        trace = [
            {"offset": 0, "name": "call", "operands": [], "targets": []},
            {"offset": 12, "name": "br.case", "operands": [], "targets": [18]},
            {"offset": 18, "name": "line", "operands": [3], "targets": []},
            {"offset": 22, "name": "ldc.i", "operands": [7], "targets": []},
            {"offset": 28, "name": "bne.case", "operands": [], "targets": [40]},
            {"offset": 34, "name": "ret", "operands": [], "targets": []},
            {"offset": 40, "name": "ret", "operands": [], "targets": []},
        ]
        offsets = {op["offset"]: i for i, op in enumerate(trace)}
        result = MJO_FLOW.menu_dispatch(trace, 0, offsets, {18, 40})
        self.assertEqual(result["cases"], [{"value": 7, "target": 34}])
        self.assertEqual(result["otherwise"], 40)

    def test_majiro_slot_frame_run_requires_matching_version_and_adjacent_records(self):
        def frame(name, pc):
            return name.ljust(128, b"\0") + struct.pack("<10I", pc, 0, 0, 0, 9, 0, 0, 0, 0, 0)

        first = frame(b"STORY.MJO", 12)
        second = frame(b"console.mjo", 20)
        def resolve(name, pc, line):
            return [{"offset": pc}] if (name, pc, line) in {
                (b"story.mjo", 12, 9), (b"console.mjo", 20, 9)
            } else []

        names = {b"story.mjo", b"console.mjo"}
        prefix = MJO_SAVE.SIGNATURE + b"header"
        runs = MJO_SAVE.match_frames(prefix + first + second, names, resolve)
        self.assertEqual([f["slot_offset"] for f in runs[0]], [len(prefix), len(prefix) + 168])
        for data in (prefix + first, prefix + first + b"gap" + second, b"MajiroSysV1.100\0" + first + second):
            with self.assertRaises(ValueError):
                MJO_SAVE.match_frames(data, names, resolve)

    def test_musica_mixed_encodings_duplicate_ids_and_branches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "edition"
            base = Path(td) / "base"
            root.mkdir()
            base.mkdir()
            first = b".if done == 1\tfinish\r\n"
            named = (b".message\t100\tvoice[50]\t@" + "太郎".encode("cp932")
                     + b"\t" + "你好".encode("gbk") + b"\\nX\r\n")
            second = b".message\t100\t\t\tNarration\r\n"
            label = b".label finish\r\n"
            path = root / "Scene.sc"
            path.write_bytes(first + named + second + label + b".chain NEXT.SC\r\n.goto missing\r\n.end")
            (base / "Next.sc").write_bytes(b";comment\n.end\n")

            report = SC.extract(root, "gbk", "cp932", base)
            one, two = report["scripts"][0]["dialogue"]
            self.assertEqual((one["speaker"], one["voice_ref"], one["text"]), ("太郎", "voice[50]", "你好\\nX"))
            self.assertTrue(one["speaker_marked"])
            self.assertIsNone(two["speaker"])
            self.assertEqual(one["message_id"], two["message_id"])
            self.assertEqual(two["byte_offset"], len(first + named))
            branch, chain, missing, end = report["control_flow"]
            self.assertEqual(branch["target"]["line"], 4)
            self.assertEqual(branch["fallthrough"]["line"], 2)
            self.assertEqual(chain["target"], {"group": "chain-base", "file": "Next.sc", "line": 2, "byte_offset": 9})
            self.assertEqual(missing["status"], "unresolved")
            self.assertEqual(end["status"], "terminal")
            self.assertFalse(report["save_slot_mapping_verified"])

            path.write_bytes(first + b".message 100 voice\n")
            with self.assertRaisesRegex(ValueError, "Scene.sc:2: message"):
                SC.extract(root, "gbk", "cp932")

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
