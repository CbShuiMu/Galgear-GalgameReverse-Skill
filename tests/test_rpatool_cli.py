"""Synthetic RPA contracts; no game, engine, or external model is started."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
TOOLS = [ROOT / skill / "tools" / "rpatool" for skill in (
    "GalgameResourceExtract", "GalgameResourcePack",
)]


def synthesize(path, members, version=3, *, data=b"abcdef", key=0x12345678):
    """Member tuples contain clear offsets relative to the start of data."""
    header_size = 34 if version == 3 else 25
    index = {}
    for name, chunks in members.items():
        index[name] = []
        for offset, length, prefix in chunks:
            stored_offset = header_size + offset
            if version == 3:
                stored_offset, length = stored_offset ^ key, length ^ key
            index[name].append((stored_offset, length, prefix))
    index_offset = header_size + len(data)
    header = (f"RPA-3.0 {index_offset:016x} {key:08x}\n" if version == 3
              else f"RPA-2.0 {index_offset:016x}\n").encode("ascii")
    path.write_bytes(header + data + zlib.compress(pickle.dumps(index, protocol=4)))


class RpaCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, tool, *args, success=True, cwd=None):
        result = subprocess.run(
            [sys.executable, str(tool / "rpatool.py"), *map(str, args)],
            cwd=cwd or self.root, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_bundles_identical_and_help(self):
        names = {p.name for p in TOOLS[0].iterdir() if p.is_file()}
        self.assertEqual(names, {p.name for p in TOOLS[1].iterdir() if p.is_file()})
        for name in names:
            self.assertEqual((TOOLS[0] / name).read_bytes(), (TOOLS[1] / name).read_bytes())
        self.assertEqual(hashlib.sha256((TOOLS[0] / "rpatool").read_bytes()).hexdigest(),
                         "d343124cebd832f712540cc6468253f7e303979467e11c7490807f42c13963f1")
        for tool in TOOLS:
            self.assertIn("extract", self.call(tool, "--help").stdout)
            self.assertIn("GalSkill CLI 1", self.call(tool, "--version").stdout)

    def test_standalone_v2_v3_roundtrip_and_empty_file(self):
        source = self.root / "input"
        (source / "images").mkdir(parents=True)
        (source / "images" / "背景.bin").write_bytes(bytes(range(256)))
        (source / "script.rpy").write_text('"合成对白"\n', encoding="utf-8")
        (source / "empty.bin").write_bytes(b"")
        for version in (2, 3):
            for i, tool in enumerate(TOOLS):
                with self.subTest(version=version, skill=i):
                    archive = self.root / f"result-{version}-{i}.rpa"
                    self.call(tool, "create", source, "-o", archive, "--format", version)
                    listing = self.call(tool, "list", archive).stdout.splitlines()
                    self.assertEqual(listing, ["empty.bin", "images/背景.bin", "script.rpy"])
                    output = self.root / f"out-{version}-{i}"
                    self.call(tool, "extract", archive, "-o", output)
                    for entry in listing:
                        self.assertEqual((source / entry).read_bytes(), (output / entry).read_bytes())

    def test_relocated_tool_has_no_repository_dependencies(self):
        source = self.root / "relocated-input"
        source.mkdir()
        (source / "item.bin").write_bytes(b"standalone fixture")
        for i, original in enumerate(TOOLS):
            installed = self.root / f"installed-{i}" / "tools" / "rpatool"
            shutil.copytree(original, installed, ignore=shutil.ignore_patterns("__pycache__"))
            archive = self.root / f"relocated-{i}.rpa"
            self.call(installed, "create", source, "-o", archive)
            output = self.root / f"relocated-result-{i}"
            self.call(installed, "extract", archive, "-o", output)
            self.assertEqual((output / "item.bin").read_bytes(), b"standalone fixture")

    def test_multichunk_prefix_and_zero_length(self):
        for version in (2, 3):
            archive = self.root / f"fragments-{version}.rpa"
            synthesize(archive, {"voice.bin": [(0, 2, b"PRE"), (2, 4, b""), (6, 0, b"END")]}, version)
            for i, tool in enumerate(TOOLS):
                with self.subTest(version=version, skill=i):
                    out = self.root / f"fragments-{version}-{i}"
                    self.call(tool, "extract", archive, "-o", out)
                    self.assertEqual((out / "voice.bin").read_bytes(), b"PREabcdefEND")
                    rebuilt = self.root / f"rebuilt-{version}-{i}.rpa"
                    self.call(tool, "create", out, "-o", rebuilt, "--format", version)
                    verified = self.root / f"verified-{version}-{i}"
                    self.call(tool, "extract", rebuilt, "-o", verified)
                    self.assertEqual((verified / "voice.bin").read_bytes(), b"PREabcdefEND")

    def test_traversal_absolute_collision_and_bounds_rejected_before_output(self):
        invalid = [
            {"../outside.bin": [(0, 1, b"")]},
            {"nested/../../outside.bin": [(0, 1, b"")]},
            {"C:/outside.bin": [(0, 1, b"")]},
            {"/outside.bin": [(0, 1, b"")]},
            {"NUL.txt": [(0, 1, b"")]},
            {"A.txt": [(0, 1, b"")], "a.txt": [(1, 1, b"")]},
            {"a": [(0, 1, b"")], "a/b": [(1, 1, b"")]},
            {"overshoot": [(5, 2, b"")]},
            {"negative": [(-35, 1, b"")]},
        ]
        for n, members in enumerate(invalid):
            archive = self.root / f"invalid-{n}.rpa"
            synthesize(archive, members)
            for i, tool in enumerate(TOOLS):
                output = self.root / f"invalid-output-{n}-{i}"
                self.call(tool, "extract", archive, "-o", output, success=False)
                self.assertFalse(output.exists())
        self.assertFalse((self.root / "outside.bin").exists())

    def test_pickle_code_and_persistent_objects_are_rejected(self):
        # A primitive-only valid pickle is deliberately followed by executable opcodes.
        marker = self.root / "executed.txt"
        payloads = [
            (f"cbuiltins\neval\n(S\"open({str(marker)!r}, 'w').write('bad')\"\ntR.").encode("utf-8"),
            b"Pexternal-object\n.",
            b"\x80\x04\x8c\x08builtins\x8c\x04eval\x93.",
        ]
        for n, payload in enumerate(payloads):
            archive = self.root / f"pickle-{n}.rpa"
            archive.write_bytes(b"RPA-3.0 0000000000000022 00000000\n" + zlib.compress(payload))
            for i, tool in enumerate(TOOLS):
                output = self.root / f"pickle-output-{n}-{i}"
                self.call(tool, "extract", archive, "-o", output, success=False)
                self.assertFalse(output.exists())
        self.assertFalse(marker.exists())

    def test_size_limit_and_existing_outputs_preserved(self):
        archive = self.root / "large.rpa"
        synthesize(archive, {"big.bin": [(0, 2 * 1024 * 1024, b"")]},
                   data=b"z" * (2 * 1024 * 1024))
        for i, tool in enumerate(TOOLS):
            output = self.root / f"limited-{i}"
            self.call(tool, "extract", archive, "-o", output, "--max-file-mib", 1, success=False)
            self.assertFalse(output.exists())
            existing = self.root / f"preserve-{i}"
            existing.mkdir()
            (existing / "big.bin").write_bytes(b"original")
            self.call(tool, "extract", archive, "-o", existing, success=False)
            self.assertEqual((existing / "big.bin").read_bytes(), b"original")

    def test_index_decompression_limit_is_enforced(self):
        archive = self.root / "oversized-index.rpa"
        packed = zlib.compress(b"\0" * (64 * 1024 * 1024 + 1))
        archive.write_bytes(b"RPA-3.0 0000000000000022 00000000\n" + packed)
        for i, tool in enumerate(TOOLS):
            output = self.root / f"oversized-index-{i}"
            self.call(tool, "extract", archive, "-o", output, success=False)
            self.assertFalse(output.exists())

    def test_source_error_is_nonzero_and_does_not_create_archive(self):
        for i, tool in enumerate(TOOLS):
            output = self.root / f"missing-{i}.rpa"
            self.call(tool, "create", self.root / "missing", "-o", output, success=False)
            self.assertFalse(output.exists())

    def test_create_rejects_output_inside_input_after_dotdot_normalization(self):
        source = self.root / "input"
        source.mkdir()
        (source / "item.bin").write_bytes(b"original input")
        sibling = self.root / "sibling"
        sibling.mkdir()
        aliased_source = sibling / ".." / "input"
        for i, tool in enumerate(TOOLS):
            target = source / f"result-{i}.rpa"
            disguised_target = sibling / ".." / "input" / target.name
            result = self.call(tool, "create", source, "-o", disguised_target, success=False)
            self.assertIn("outside input directory", result.stderr)
            self.assertFalse(target.exists())
            result = self.call(tool, "create", aliased_source, "-o", target, success=False)
            self.assertIn("outside input directory", result.stderr)
            self.assertFalse(target.exists())
        self.assertEqual((source / "item.bin").read_bytes(), b"original input")

    def test_create_rejects_parent_links_before_canonicalization(self):
        source = self.root / "input"
        source.mkdir()
        (source / "item.bin").write_bytes(b"source")
        real = self.root / "real"
        real.mkdir()
        link = self.root / "linked-parent"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                self.skipTest("directory symlinks are unavailable")
            junction = subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(link), str(real)],
                capture_output=True,
            )
            if junction.returncode:
                self.skipTest("directory symlinks and junctions are unavailable")
        for i, tool in enumerate(TOOLS):
            target = link / f"result-{i}.rpa"
            result = self.call(tool, "create", source, "-o", target, success=False)
            self.assertIn("links and directory junctions", result.stderr)
            self.assertFalse((real / target.name).exists())
            disguised = link / ".." / f"outside-{i}.rpa"
            result = self.call(tool, "create", source, "-o", disguised, success=False)
            self.assertIn("links and directory junctions", result.stderr)
            self.assertFalse((self.root / disguised.name).exists())


if __name__ == "__main__":
    unittest.main()
