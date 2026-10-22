"""Synthetic checks for the independently installed GalArc CLI subsets."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("GalgameResourceExtract", "GalgameResourcePack")


def inventory(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*") if p.is_file()
    }


class GalArcCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="galarc-cli-test-")
        self.base = Path(self.temp.name)
        self.exe = ROOT / SKILLS[0] / "tools/galarc-cli/galarc.exe"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, success=True, exe=None):
        proc = subprocess.run(
            [str(exe or self.exe), *map(str, args)], capture_output=True,
            text=True, encoding="utf-8", errors="replace", cwd=self.base,
        )
        if success:
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        else:
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def inputs(self, nested):
        source = self.base / "input"
        source.mkdir()
        (source / "voice01.bin").write_bytes(bytes(range(256)) * 3)
        (source / "日本語.txt").write_bytes("合成データ\n".encode("cp932"))
        (source / "empty.bin").write_bytes(b"")
        if nested:
            (source / "sub").mkdir()
            (source / "sub" / "voice02.bin").write_bytes(b"nested\x00data")
        return source

    def test_both_installations_are_standalone_and_identical(self):
        expected = inventory(ROOT / SKILLS[0] / "tools/galarc-cli")
        for skill in SKILLS:
            folder = ROOT / skill / "tools/galarc-cli"
            self.assertEqual(inventory(folder), expected)
            isolated = self.base / skill
            isolated.mkdir()
            local_exe = isolated / "galarc.exe"
            local_exe.write_bytes((folder / "galarc.exe").read_bytes())
            proc = self.run_cli("--help", exe=local_exe)
            self.assertIn("NOA", proc.stdout)
            self.assertFalse(any("gui" in p.name.casefold() for p in folder.rglob("*")))
            self.assertTrue((folder / "LICENSE.txt").is_file())
            self.assertTrue((folder / "source/Program.cs").is_file())

    def roundtrip(self, format, nested):
        source = self.inputs(nested)
        output = self.base / ("result." + format)
        arguments = ["pack", format, source, output]
        if format == "noa":
            arguments.append("--raw")
        self.run_cli(*arguments)
        listed = json.loads(self.run_cli("list", format, output).stdout)
        self.assertEqual(len(listed), len(inventory(source)))
        extracted = self.base / "extracted"
        self.run_cli("extract", format, output, extracted)
        self.assertEqual(inventory(extracted), inventory(source))
        garbro = ROOT / SKILLS[0] / "tools/GARbro-cli/GARbro.Console.exe"
        independent = self.base / "garbro"
        proc = subprocess.run(
            [str(garbro), "x", "-q", "-y", "-o", str(independent), str(output)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(inventory(independent), inventory(source))

    def test_ns2_recursive_roundtrip_and_independent_read(self):
        self.roundtrip("ns2", True)

    def test_noa_raw_roundtrip_and_independent_read(self):
        self.roundtrip("noa", False)

    def test_noa_requires_explicit_raw_and_rejects_subdirectories(self):
        source = self.inputs(True)
        output = self.base / "out.noa"
        self.assertEqual(self.run_cli("pack", "noa", source, output, success=False).returncode, 2)
        self.run_cli("pack", "noa", source, output, "--raw", success=False)
        self.assertFalse(output.exists())

    def test_outputs_never_overwrite_and_failures_leave_no_partial_output(self):
        source = self.inputs(False)
        output = self.base / "result.ns2"
        self.run_cli("pack", "ns2", source, output)
        original = output.read_bytes()
        self.run_cli("pack", "ns2", source, output, success=False)
        self.assertEqual(output.read_bytes(), original)
        destination = self.base / "existing"
        destination.mkdir()
        (destination / "sentinel").write_bytes(b"keep")
        self.run_cli("extract", "ns2", output, destination, success=False)
        self.assertEqual((destination / "sentinel").read_bytes(), b"keep")
        truncated = self.base / "bad.ns2"
        truncated.write_bytes(original[:-1])
        missing = self.base / "bad-output"
        self.run_cli("extract", "ns2", truncated, missing, success=False)
        self.assertFalse(missing.exists())
        self.assertFalse(list(self.base.glob(".galarc-*")))

    @staticmethod
    def make_ns2(name, payload=b"x"):
        encoded = name.encode("cp932")
        index = b'"' + encoded + b'"' + struct.pack("<I", len(payload)) + b"e"
        return struct.pack("<I", len(index) + 4) + index + payload

    def test_unsafe_ns2_paths_and_invalid_encoding_are_rejected_before_writing(self):
        for number, name in enumerate(("../escape.bin", "C:\\escape.bin", "CON", "trailing. ", "x/../bad")):
            archive = self.base / f"unsafe{number}.ns2"
            archive.write_bytes(self.make_ns2(name))
            target = self.base / f"unsafe-out{number}"
            self.run_cli("extract", "ns2", archive, target, success=False)
            self.assertFalse(target.exists())
        archive = self.base / "invalid-encoding.ns2"
        archive.write_bytes(struct.pack("<I", 12) + b'"\x81"' + struct.pack("<I", 1) + b"e" + b"x")
        self.run_cli("list", "ns2", archive, success=False)
        self.assertFalse((self.base / "escape.bin").exists())

    def test_noa_rejects_encoded_or_out_of_bounds_entries(self):
        source = self.inputs(False)
        archive = self.base / "raw.noa"
        self.run_cli("pack", "noa", source, archive, "--raw")
        original = bytearray(archive.read_bytes())
        for number, (offset, value) in enumerate(((96, 1), (100, 0x7FFFFFFF))):
            content = bytearray(original)
            struct.pack_into("<I", content, offset, value)
            malformed = self.base / f"bad{number}.noa"
            malformed.write_bytes(content)
            target = self.base / f"bad-noa-out{number}"
            self.run_cli("extract", "noa", malformed, target, success=False)
            self.assertFalse(target.exists())

    def test_input_links_are_rejected(self):
        source = self.inputs(False)
        link = source / "link.bin"
        try:
            link.symlink_to(source / "voice01.bin")
        except OSError as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        output = self.base / "link.ns2"
        self.run_cli("pack", "ns2", source, output, success=False)
        self.assertFalse(output.exists())

    def test_unencodable_names_are_rejected_before_creating_archive(self):
        source = self.inputs(False)
        (source / "emoji-😀.bin").write_bytes(b"test")
        output = self.base / "encoding.ns2"
        self.run_cli("pack", "ns2", source, output, success=False)
        self.assertFalse(output.exists())

    def test_noncanonical_cp932_name_bytes_are_rejected_before_output(self):
        # CP932 87 90 and 81 E0 both decode to U+2252; the Windows encoder
        # emits 81 E0 (strict .NET Framework may reject 87 90 at decoding).
        # Accepting the alias must never silently change archive name bytes.
        raw_name = b"\x87\x90.bin"
        payload = b"synthetic member"
        ns2_index = b'"' + raw_name + b'"' + struct.pack("<I", len(payload)) + b"e"
        ns2 = struct.pack("<I", len(ns2_index) + 4) + ns2_index + payload
        index_size = 4 + 40 + len(raw_name) + 1
        noa_header = bytearray(64)
        noa_header[:16] = bytes.fromhex("456e7469731a00000004000200000000")
        noa_header[16:34] = b"ERISA-Archive file"
        noa_index = (b"DirEntry" + struct.pack("<QI", index_size, 1)
                     + struct.pack("<QIIQQII", len(payload), 0, 0, 16 + index_size, 0, 0, len(raw_name) + 1)
                     + raw_name + b"\0")
        noa = noa_header + noa_index + b"filedata" + struct.pack("<Q", len(payload)) + payload
        struct.pack_into("<Q", noa, 56, len(noa) - 64)
        for format, content in (("ns2", ns2), ("noa", noa)):
            archive = self.base / ("alias." + format)
            archive.write_bytes(content)
            self.run_cli("list", format, archive, success=False)
            target = self.base / ("alias-output-" + format)
            self.run_cli("extract", format, archive, target, success=False)
            self.assertFalse(target.exists())
            self.assertEqual(archive.read_bytes(), content)

    def test_dot_paths_cannot_hide_output_inside_input(self):
        source = self.inputs(False)
        sibling = self.base / "sibling"
        sibling.mkdir()
        target = sibling / ".." / source.name / "result.ns2"
        result = self.run_cli("pack", "ns2", source, target, success=False)
        self.assertIn("outside input", result.stderr)
        self.assertFalse((source / "result.ns2").exists())
        # Benign parent components are accepted after canonical validation.
        archive = self.base / "normal.ns2"
        self.run_cli("pack", "ns2", sibling / ".." / source.name, archive)
        self.assertTrue(archive.is_file())

    def test_parent_links_including_cancelled_components_are_rejected(self):
        source = self.inputs(False)
        archive = self.base / "plain.ns2"
        self.run_cli("pack", "ns2", source, archive)
        real = self.base / "real"
        real.mkdir()
        alias = self.base / "alias"
        try:
            alias.symlink_to(real, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        for target in (alias / "out.ns2", alias / ".." / "cancelled.ns2"):
            self.run_cli("pack", "ns2", source, target, success=False)
        for target in (alias / "out", alias / ".." / "cancelled-output"):
            self.run_cli("extract", "ns2", archive, target, success=False)
        self.run_cli("list", "ns2", alias / ".." / archive.name, success=False)
        self.assertEqual(list(real.iterdir()), [])
        self.assertFalse((self.base / "cancelled.ns2").exists())
        self.assertFalse((self.base / "cancelled-output").exists())


if __name__ == "__main__":
    unittest.main()
