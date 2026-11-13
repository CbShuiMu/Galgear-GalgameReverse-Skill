"""Mod error handling, extraction destinations and removal of the old pack backend."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'resource_workflow_mod', ROOT / 'GalgameResourcePack/scripts/resource_workflow.py')
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)
CLI = ROOT / 'GalgameResourcePack/tools/GARbro-cli/GARbro.Console.exe'


class RemovedPackBackendTests(unittest.TestCase):
    def test_pack_fails_before_reading_manifest_or_creating_artifacts(self):
        with self.assertRaisesRegex(ValueError, 'does not support archive creation'):
            workflow.pack_or_verify(SimpleNamespace(command='pack'))


@unittest.skipUnless(sys.platform == 'win32', 'Windows .NET Framework CLI required')
class ModVerificationTests(unittest.TestCase):
    def test_extracts_to_fresh_directory_and_checks_members(self):
        with tempfile.TemporaryDirectory(prefix='mod-verify-') as td:
            base = Path(td)
            archive = base / 'synthetic archive.zip'
            content = b'synthetic archive payload'
            with zipfile.ZipFile(archive, 'w') as output:
                output.writestr('nested/same.bin', content)
            value = dict(resource_root=str(base/'staged'), original_root=str(base/'raw'),
                         generated_root=str(base/'generated'), mode='full', archive={'format': 'ZIP'},
                         entries=[dict(path='nested/same.bin', action='retained',
                                       expected_sha256=hashlib.sha256(content).hexdigest())])
            cwd = Path.cwd()
            report = workflow.verify_output(value, archive, CLI, base / 'check')
            self.assertTrue(report['passed'], report)
            self.assertEqual(Path.cwd(), cwd)
            self.assertEqual((base/'check/nested/same.bin').read_bytes(), content)
            value['entries'][0]['expected_sha256'] = '0' * 64
            self.assertFalse(workflow.verify_output(value, archive, CLI, base/'bad-hash')['passed'])
            with self.assertRaises(FileExistsError):
                workflow.verify_output(value, archive, CLI, base/'check')

    def test_rejects_mod_zero_exit_with_error_diagnostic(self):
        with tempfile.TemporaryDirectory(prefix='mod-error-') as td:
            base = Path(td)
            archive = base/'invalid.zip'
            archive.write_bytes(b'not an archive')
            with self.assertRaisesRegex(RuntimeError, 'GARbro Mod failed'):
                workflow.cli(CLI, ['-x', archive], cwd=base)


if __name__ == '__main__':
    unittest.main()
