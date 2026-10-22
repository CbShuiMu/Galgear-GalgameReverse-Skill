"""Exercise stored RealLive archive members in temporary skill copies."""
from pathlib import Path
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SeenTests(unittest.TestCase):
    def call(self, tool, *args, success=True):
        result = subprocess.run([sys.executable, str(tool), *map(str, args)],
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode == 0, success, result.stderr.decode(errors='replace'))
        return json.loads(result.stdout) if success else result

    def test_standalone_roundtrip_and_boundaries(self):
        for folder in ('GalgameResourceExtract', 'GalgameResourcePack'):
            with self.subTest(skill=folder), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                shutil.copytree(ROOT / folder / 'tools/rldev-seen', root / 'tool')
                tool = root / 'tool/rlseen.py'
                members = root / 'members'
                members.mkdir()
                fixture = {'SEEN0001.TXT': struct.pack('<II', 0x1d0, 10002) + b'fixture-one',
                           'SEEN9999.TXT': struct.pack('<II', 0x1d0, 10002) + bytes(range(256))}
                for name, content in fixture.items():
                    (members / name).write_bytes(content)
                archive = root / 'SEEN.TXT'
                self.call(tool, 'pack', members, archive)
                self.assertEqual([row['slot'] for row in self.call(tool, 'list', archive)['entries']], [1, 9999])
                output = root / 'unpacked'
                self.call(tool, 'unpack', archive, output)
                self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, fixture)
                saved = archive.read_bytes()
                self.call(tool, 'pack', members, archive, success=False)
                self.assertEqual(archive.read_bytes(), saved)
                self.call(tool, 'unpack', archive, output, success=False)
                self.call(tool, '--max-bytes', 80000, 'unpack', archive, root / 'limited', success=False)
                self.assertFalse((root / 'limited').exists())
                bad = bytearray(saved)
                struct.pack_into('<II', bad, 8, len(bad) - 1, 999)
                (root / 'bad.seen').write_bytes(bad)
                self.call(tool, 'unpack', root / 'bad.seen', root / 'bad-out', success=False)
                self.assertFalse((root / 'bad-out').exists())
                (members / 'unexpected.txt').write_bytes(b'unexpected')
                self.call(tool, 'pack', members, root / 'unexpected.seen', success=False)
                self.assertFalse((root / 'unexpected.seen').exists())
                (members / 'unexpected.txt').unlink()
                (root / 'sibling').mkdir()
                self.call(tool, 'pack', members, root / 'sibling/../members/output.seen', success=False)
                self.assertFalse((members / 'output.seen').exists())
                (members / 'SEEN0002.TXT').write_bytes(b'KPRL' + b'working-copy')
                self.call(tool, 'pack', members, root / 'working.seen', success=False)
                self.assertFalse((root / 'working.seen').exists())

    def test_reject_parent_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / 'actual'
            actual.mkdir()
            link = root / 'linked'
            try:
                link.symlink_to(actual, target_is_directory=True)
            except OSError:
                self.skipTest('Directory symlinks unavailable in this environment')
            tool = ROOT / 'GalgameResourceExtract/tools/rldev-seen/rlseen.py'
            members = root / 'members'
            members.mkdir()
            (members / 'SEEN0001.TXT').write_bytes(b'synthetic stored member')
            archive = root / 'SEEN.TXT'
            self.call(tool, 'pack', members, archive)
            self.call(tool, 'unpack', archive, link / 'unpacked', success=False)
            self.call(tool, 'pack', members, link / 'output.seen', success=False)
            self.assertEqual(list(actual.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
