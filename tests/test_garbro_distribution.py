"""Exercise the pinned upstream CLI after copying each skill's runtime alone."""
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('GalgameResourceExtract', 'GalgameResourcePack')


@unittest.skipUnless(sys.platform == 'win32', 'Windows .NET Framework CLI required')
class GarbroDistributionTests(unittest.TestCase):
    def test_isolated_release_lists_and_extracts_exact_members(self):
        for skill in SKILLS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory(prefix='garbro-mod-') as td:
                base = Path(td)
                bundled = ROOT / skill / 'tools/GARbro-cli'
                installed = base / 'installed tool'
                shutil.copytree(bundled, installed,
                                ignore=shutil.ignore_patterns('source', 'licenses'))
                cli = installed / 'GARbro.Console.exe'

                def run(*arguments, cwd=base):
                    result = subprocess.run([str(cli), *map(str, arguments)], cwd=cwd,
                                            capture_output=True, timeout=30,
                                            encoding='utf-8-sig', errors='replace')
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stderr.strip(), '', result.stderr)
                    return result.stdout

                self.assertIn('Usage:', run())
                self.assertIn('ZIP', run('-l'))
                fixture = {'nested/same.bin': b'synthetic\0payload',
                           'other/same.bin': bytes(range(256)), 'empty.dat': b''}
                archive = base / 'synthetic archive.zip'
                with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
                    for name, data in fixture.items():
                        output.writestr(name, data)
                listed = run(archive)
                for name in fixture:
                    self.assertIn(name, listed)
                extracted = base / 'raw'
                extracted.mkdir()
                run('-x', archive, cwd=extracted)
                actual = {p.relative_to(extracted).as_posix(): p.read_bytes()
                          for p in extracted.rglob('*') if p.is_file()}
                self.assertEqual(actual, fixture)
                selected = base / 'selected'
                selected.mkdir()
                run(archive, 'NESTED/SAME.BIN', cwd=selected)
                self.assertEqual((selected / 'nested/same.bin').read_bytes(), fixture['nested/same.bin'])
                self.assertEqual(len(list(selected.rglob('*.bin'))), 1)

    def test_pinned_files_and_source_match_recorded_hashes(self):
        manifests = []
        for skill in SKILLS:
            bundled = ROOT / skill / 'tools/GARbro-cli'
            self.assertFalse((bundled / 'legacy').exists(), 'Only the Mod runtime may be bundled')
            manifest = json.loads((bundled / 'provenance.json').read_text('utf-8'))
            self.assertNotIn('legacy', manifest)
            manifests.append(manifest['files'])
            self.assertIn('source/GARbro-Mod-1.0.2.2.zip', manifest['files'])
            for name, digest in manifest['files'].items():
                with self.subTest(skill=skill, file=name):
                    self.assertEqual(hashlib.sha256((bundled / name).read_bytes()).hexdigest(), digest)
            self.assertFalse(list(bundled.glob('GARbro.GUI*')))
            self.assertFalse(list(bundled.glob('*/GARbro.GUI.resources.dll')))
        self.assertEqual(manifests[0], manifests[1])

    def test_image_helper_provenance_matches_mod_runtime(self):
        bundled = ROOT / 'GalgameResourceExtract/tools/GARbro-cli'
        manifest = json.loads((bundled / 'image-cli-provenance.json').read_text('utf-8'))
        self.assertEqual(manifest['runtime'], 'GARbro-Mod-1.0.2.2')
        for name, digest in manifest['files'].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((bundled / name).read_bytes()).hexdigest(), digest)
        self.assertEqual((bundled / 'GalImageExport.exe.config').read_bytes(),
                         (bundled / 'GARbro.Console.exe.config').read_bytes())


if __name__ == '__main__':
    unittest.main()
