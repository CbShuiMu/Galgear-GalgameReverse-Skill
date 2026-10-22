"""Synthetic Majiro V3 checks; no game code, media, or model is executed."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = [ROOT / skill / 'tools/majiro-cli' for skill in
         ('GalgameResourceExtract', 'GalgameResourcePack')]


def reference_hash64(data):
    # Independent bitwise recurrence, as documented by the reversing authors.
    value = 0xFFFFFFFFFFFFFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0x42F0E1EBA9EA3693 if value & 1 else 0)
    return value ^ 0xFFFFFFFFFFFFFFFF


def make_v3(rows):
    """Rows = raw CP932 filename bytes and payload; independent fixture writer."""
    sorted_rows = sorted((reference_hash64(name), name, data) for name, data in rows)
    names = b''.join(name + b'\0' for _, name, _ in sorted_rows)
    data_at = 28 + 16 * len(rows) + len(names)
    table = bytearray()
    body = bytearray()
    for hashed, name, data in sorted_rows:
        table += struct.pack('<QII', hashed, data_at + len(body), len(data))
        body += data
    return (b'MajiroArcV3.000\0' + struct.pack('<III', len(rows), 28 + 16 * len(rows), data_at)
            + table + names + body)


def inventory(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


class MajiroCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='majiro-cli-test-')
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, tool, *args, success=True):
        proc = subprocess.run([sys.executable, '-B', str(tool / 'majiro_cli.py'), *map(str, args)],
                              cwd=self.base, capture_output=True, timeout=30,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(proc.returncode == 0, success, proc.stderr.decode(errors='replace'))
        return proc

    def inputs(self):
        source = self.base / 'input'
        source.mkdir()
        fixture = {'b.mjo': bytes(range(256)), 'a.bin': b'data\0stored',
                   '日本語.txt': '合成'.encode('cp932'), 'empty.dat': b''}
        for name, data in fixture.items():
            (source / name).write_bytes(data)
        return source, fixture

    def test_bundle_sources_identical_and_original_hash_library(self):
        self.assertEqual(inventory(TOOLS[0]), inventory(TOOLS[1]))
        for tool in TOOLS:
            self.assertIn(b'ARC V3', self.call(tool, '--version').stdout)
            data = json.loads((tool / 'SOURCE.json').read_text(encoding='utf-8'))
            for path, digest in data['files'].items():
                self.assertEqual(hashlib.sha256((tool / path).read_bytes()).hexdigest(), digest)
            self.assertTrue((tool / 'licenses/NarciBloom-MIT.txt').is_file())
            self.assertTrue((tool / 'licenses/majiro-py-MIT.txt').is_file())
            self.assertFalse(any('gui' in p.name.casefold() for p in tool.rglob('*')))

    def test_crc64_values_match_original_library_and_independent_recurrence(self):
        cases = [b'', b'123456789', b'a.bin', '日本語.txt'.encode('cp932'), bytes(range(256))]
        code = ('import json,sys;sys.path.insert(0,sys.argv[1]);'
                'from mjotool.crypt import hash64;'
                'print(json.dumps([hash64(bytes.fromhex(x)) for x in sys.argv[2:]]))')
        proc = subprocess.run([sys.executable, '-B', '-c', code,
                               str(TOOLS[0] / 'source/majiro-py/src'),
                               *(value.hex() for value in cases)], capture_output=True, check=True)
        original = json.loads(proc.stdout)
        self.assertEqual(original, [reference_hash64(value) for value in cases])
        self.assertEqual(original[0], 0)
        # Verify the non-standard variant instead of any CRC64-ECMA library default.
        self.assertNotEqual(original[1], 0x6C40DF5F0B497347)

    def test_standalone_roundtrip_hash_order_and_independent_garbro(self):
        source, fixture = self.inputs()
        for number, original in enumerate(TOOLS):
            installed = self.base / f'installed-{number}'
            shutil.copytree(original, installed, ignore=shutil.ignore_patterns('__pycache__'))
            archive = self.base / f'rebuilt-{number}.arc'
            self.call(installed, 'pack', source, archive)
            raw = archive.read_bytes()
            count, names_at, data_at = struct.unpack_from('<III', raw, 16)
            rows = list(struct.iter_unpack('<QII', raw[28:names_at]))
            names = raw[names_at:data_at].split(b'\0')[:-1]
            self.assertEqual(count, len(fixture))
            self.assertEqual([row[0] for row in rows], sorted(row[0] for row in rows))
            self.assertEqual([row[0] for row in rows], [reference_hash64(name) for name in names])
            for name, (_, offset, size) in zip(names, rows):
                self.assertEqual(raw[offset:offset + size], fixture[name.decode('cp932')])
            listed = json.loads(self.call(installed, 'list', archive).stdout)
            self.assertEqual(listed['count'], len(fixture))
            output = self.base / f'extracted-{number}'
            self.call(installed, 'extract', archive, output)
            self.assertEqual(inventory(output), inventory(source))
            independent = self.base / f'garbro-{number}'
            garbro = ROOT / 'GalgameResourceExtract/tools/GARbro-cli/GARbro.Console.exe'
            proc = subprocess.run([str(garbro), 'x', '-q', '-y', '-o', str(independent), str(archive)],
                                  capture_output=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors='replace'))
            self.assertEqual(inventory(independent), inventory(source))

    def test_reader_accepts_independent_fixture_and_empty_members(self):
        archive = self.base / 'fixture.arc'
        archive.write_bytes(make_v3([(b'empty.dat', b''), (b'item.bin', b'payload')]))
        self.call(TOOLS[0], 'extract', archive, self.base / 'output')
        self.assertEqual((self.base / 'output/empty.dat').read_bytes(), b'')
        self.assertEqual((self.base / 'output/item.bin').read_bytes(), b'payload')

    def test_uppercase_unencodable_and_subdirectory_input_rejected(self):
        for number, name in enumerate(('UPPER.bin', 'unicode-😀.bin', '〜.bin')):
            source = self.base / f'input-{number}'
            source.mkdir()
            (source / name).write_bytes(b'test')
            output = self.base / f'bad-{number}.arc'
            self.call(TOOLS[0], 'pack', source, output, success=False)
            self.assertFalse(output.exists())
        source = self.base / 'nested'
        source.mkdir()
        (source / 'sub').mkdir()
        self.call(TOOLS[0], 'pack', source, self.base / 'nested.arc', success=False)
        self.assertFalse((self.base / 'nested.arc').exists())

    def test_unsafe_names_alias_bytes_and_wrong_versions_rejected_before_output(self):
        bad_names = [b'../escape.bin', b'c:\\escape.bin', b'/absolute.bin', b'nul.txt',
                     b'bad. ', b'UPPER.bin', b'\x87\x90.bin']
        for number, raw_name in enumerate(bad_names):
            archive = self.base / f'bad-name-{number}.arc'
            archive.write_bytes(make_v3([(raw_name, b'data')]))
            output = self.base / f'bad-output-{number}'
            self.call(TOOLS[0], 'extract', archive, output, success=False)
            self.assertFalse(output.exists())
        for version in (1, 2):
            archive = self.base / f'wrong-v{version}.arc'
            content = bytearray(make_v3([(b'item.bin', b'data')]))
            content[10] = ord(str(version))
            archive.write_bytes(content)
            self.call(TOOLS[0], 'list', archive, success=False)

    def test_hash_sort_bounds_and_name_boundaries_rejected(self):
        original = make_v3([(b'a.bin', b'a'), (b'b.bin', b'b')])
        malformed = []
        bad_hash = bytearray(original)
        struct.pack_into('<Q', bad_hash, 28, 0)
        malformed.append(bad_hash)
        bad_order = bytearray(original)
        bad_order[28:44], bad_order[44:60] = bad_order[44:60], bad_order[28:44]
        malformed.append(bad_order)
        bad_offset = bytearray(original)
        struct.pack_into('<I', bad_offset, 36, len(original) + 1)
        malformed.append(bad_offset)
        bad_name = bytearray(original)
        struct.pack_into('<I', bad_name, 20, 61)
        malformed.append(bad_name)
        malformed.append(original[:-1])
        for number, content in enumerate(malformed):
            archive = self.base / f'malformed-{number}.arc'
            archive.write_bytes(content)
            output = self.base / f'malformed-out-{number}'
            self.call(TOOLS[0], 'extract', archive, output, success=False)
            self.assertFalse(output.exists())

    def test_existing_outputs_and_inside_input_dot_paths_rejected(self):
        source, _ = self.inputs()
        archive = self.base / 'existing.arc'
        archive.write_bytes(b'keep')
        self.call(TOOLS[0], 'pack', source, archive, success=False)
        self.assertEqual(archive.read_bytes(), b'keep')
        valid = self.base / 'valid.arc'
        self.call(TOOLS[0], 'pack', source, valid)
        output = self.base / 'existing-output'
        output.mkdir()
        (output / 'sentinel').write_bytes(b'keep')
        self.call(TOOLS[0], 'extract', valid, output, success=False)
        self.assertEqual((output / 'sentinel').read_bytes(), b'keep')
        sibling = self.base / 'sibling'
        sibling.mkdir()
        target = sibling / '..' / source.name / 'inside.arc'
        self.call(TOOLS[0], 'pack', source, target, success=False)
        self.assertFalse((source / 'inside.arc').exists())

    def test_parent_and_cancelled_links_rejected(self):
        source, _ = self.inputs()
        target = self.base / 'target'
        target.mkdir()
        alias = self.base / 'alias'
        try:
            alias.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(str(error))
        for output in (alias / 'out.arc', alias / '..' / 'cancelled.arc'):
            self.call(TOOLS[0], 'pack', source, output, success=False)
        self.assertFalse((self.base / 'cancelled.arc').exists())
        self.assertEqual(list(target.iterdir()), [])

    def test_byte_limit_rejects_before_output(self):
        source, _ = self.inputs()
        output = self.base / 'limited.arc'
        self.call(TOOLS[0], '--max-bytes', 60, 'pack', source, output, success=False)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
