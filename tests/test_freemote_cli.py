"""Run the trimmed FreeMote CLI on synthetic PSB/SCN and MDF files only."""
from pathlib import Path
import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Bundled FreeMote requires Windows .NET Framework 4.8')
class FreeMoteTests(unittest.TestCase):
    def run_cli(self, tool, executable, *arguments, cwd):
        result = subprocess.run([str(tool / executable), *map(str, arguments)], cwd=cwd,
                                capture_output=True, timeout=30)
        output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn('is not used', output, output)
        self.assertNotIn('Exception', output, output)
        return output

    def test_relocated_versions_resources_and_mdf(self):
        for skill in ('GalgameResourceExtract', 'GalgameResourcePack'):
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                tool = root / 'installed/tools/freemote'
                shutil.copytree(ROOT / skill / 'tools/freemote', tool)
                for executable in ('PsBuild.exe', 'PsbDecompile.exe'):
                    self.assertIn('Usage:', self.run_cli(tool, executable, '--help', cwd=root))
                self.assertFalse(list(tool.glob('*Viewer*')))
                self.assertFalse((tool / 'FreeMote.NET.dll').exists())
                for version in (2, 3, 4):
                    with self.subTest(version=version):
                        work = root / f'v{version}'
                        work.mkdir()
                        content = {'scenes': [], 'name': '合成テスト', 'spec': 'win', 'blob': '#resource#0',
                                   'values': [True, None, 123, -456, 1.5, '你好']}
                        resource = bytes(range(256)) * 3
                        source = work / 'fixture.json'
                        source.write_text(json.dumps(content, ensure_ascii=False, sort_keys=True), encoding='utf-8')
                        (work / 'blob.bin').write_bytes(resource)
                        (work / 'fixture.resx.json').write_text(json.dumps({
                            'PsbVersion': version, 'PsbType': 'Scn', 'Platform': 'win',
                            'Context': {}, 'Resources': {'blob': 'blob.bin'}}), encoding='utf-8')
                        psb = work / 'fixture.scn'
                        self.run_cli(tool, 'PsBuild.exe', '-ns', '-o', psb, source, cwd=root)
                        self.assertEqual(psb.read_bytes()[:6], b'PSB\0' + struct.pack('<H', version))
                        output = work / 'decoded'
                        self.run_cli(tool, 'PsbDecompile.exe', '-raw', '-t', 'Scn', '-o', output, psb, cwd=root)
                        self.assertEqual(json.loads((output / 'fixture.json').read_text('utf-8-sig')), content)
                        meta = json.loads((output / 'fixture.resx.json').read_text('utf-8-sig'))
                        self.assertEqual(meta['PsbVersion'], version)
                        self.assertEqual((output / meta['Resources']['0']).read_bytes(), resource)
                        rebuilt = work / 'rebuilt.scn'
                        self.run_cli(tool, 'PsBuild.exe', '-ns', '-o', rebuilt, output / 'fixture.json', cwd=root)
                        self.assertEqual(rebuilt.read_bytes(), psb.read_bytes())
                        if version == 3:
                            mdf = work / 'shell.mdf'
                            original = psb.read_bytes()
                            mdf.write_bytes(b'mdf\0' + struct.pack('<I', len(original)) + zlib.compress(original))
                            shell_output = work / 'shell-decoded'
                            self.run_cli(tool, 'PsbDecompile.exe', '-raw', '-t', 'Scn', '-o', shell_output, mdf, cwd=root)
                            self.assertEqual(json.loads((shell_output / 'shell.json').read_text('utf-8-sig')), content)
                            shell_rebuilt = work / 'rebuilt.mdf'
                            self.run_cli(tool, 'PsBuild.exe', '-o', shell_rebuilt, shell_output / 'shell.json', cwd=root)
                            packed = shell_rebuilt.read_bytes()
                            self.assertEqual(packed[:4], b'mdf\0')
                            self.assertEqual(zlib.decompress(packed[8:]), original)


if __name__ == '__main__':
    unittest.main()
