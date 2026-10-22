"""Exercise bundled Siglus CLIs with synthetic archives; no game is launched."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("GalgameResourceExtract", "GalgameResourcePack")
HEADER_FIELDS = (
    "header_size", "inc_prop_list_ofs", "inc_prop_cnt",
    "inc_prop_name_index_list_ofs", "inc_prop_name_index_cnt", "inc_prop_name_list_ofs", "inc_prop_name_cnt",
    "inc_cmd_list_ofs", "inc_cmd_cnt", "inc_cmd_name_index_list_ofs", "inc_cmd_name_index_cnt", "inc_cmd_name_list_ofs", "inc_cmd_name_cnt",
    "scn_name_index_list_ofs", "scn_name_index_cnt", "scn_name_list_ofs", "scn_name_cnt",
    "scn_data_index_list_ofs", "scn_data_index_cnt", "scn_data_list_ofs", "scn_data_cnt",
    "scn_data_exe_angou_mod", "original_source_header_size",
)


def synthetic_dat(payload):
    """A bounded, synthetic 132-byte SCN header and an opaque code section."""
    header = [0] * 33
    header[:3] = [132, 132, len(payload)]
    return struct.pack("<33i", *header) + payload


def synthetic_pck(names, payloads, source_tail=b""):
    """Independent fixture containing nonempty include property/command tables."""
    header = dict.fromkeys(HEADER_FIELDS, 0)
    header.update(header_size=92, inc_prop_cnt=1, inc_prop_name_index_cnt=1,
                  inc_prop_name_cnt=1, inc_cmd_cnt=1, inc_cmd_name_index_cnt=1,
                  inc_cmd_name_cnt=1, scn_name_index_cnt=len(names),
                  scn_name_cnt=len(names), scn_data_index_cnt=len(names),
                  scn_data_cnt=len(names), original_source_header_size=4 if source_tail else 0)
    result = bytearray(92)

    def add(key, data):
        header[key] = len(result)
        result.extend(data)

    add("inc_prop_list_ofs", struct.pack("<ii", 10, 1))
    add("inc_prop_name_index_list_ofs", struct.pack("<ii", 0, 8))
    add("inc_prop_name_list_ofs", "testprop".encode("utf-16le"))
    add("inc_cmd_list_ofs", struct.pack("<ii", 0, 0))
    add("inc_cmd_name_index_list_ofs", struct.pack("<ii", 0, 7))
    add("inc_cmd_name_list_ofs", "testcmd".encode("utf-16le"))
    indices, text, offset = [], bytearray(), 0
    for name in names:
        raw = name.encode("utf-16le")
        indices.extend((offset, len(raw) // 2))
        offset += len(raw) // 2
        text.extend(raw)
    add("scn_name_index_list_ofs", struct.pack("<" + "i" * len(indices), *indices))
    add("scn_name_list_ofs", text)
    data_index, offset = [], 0
    for data in payloads:
        data_index.extend((offset, len(data)))
        offset += len(data)
    add("scn_data_index_list_ofs", struct.pack("<" + "i" * len(data_index), *data_index))
    add("scn_data_list_ofs", b"".join(payloads))
    result.extend(source_tail)
    struct.pack_into("<23i", result, 0, *(header[key] for key in HEADER_FIELDS))
    return bytes(result), header


@unittest.skipUnless(os.name == "nt", "bundled CLI targets Windows x64")
class SiglusCliTests(unittest.TestCase):
    def directory_link(self, link, target):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                                    capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(link.is_symlink() or link.is_junction())

    def run_cli(self, cli, cwd, *args, success=True):
        result = subprocess.run([str(cli), *map(str, args)], cwd=cwd,
                                capture_output=True, encoding="utf-8", errors="replace",
                                timeout=45, env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def isolated_cli(self, skill, root):
        tool = ROOT / skill / "tools" / "siglus-ssu"
        isolated = root / "tool"
        isolated.mkdir()
        # The executable alone includes Python, the adapter and upstream modules.
        shutil.copy2(tool / "siglus-ssu.exe", isolated / "siglus-ssu.exe")
        return isolated / "siglus-ssu.exe"

    def test_help_version_and_identical_installations(self):
        hashes = set()
        for skill in SKILLS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory(prefix="siglus-help-") as tmp:
                root = Path(tmp)
                cli = self.isolated_cli(skill, root)
                hashes.add(hashlib.sha256(cli.read_bytes()).hexdigest())
                self.assertIn("--base", self.run_cli(cli, root, "pack", "--help").stdout)
                self.assertIn("0.5.7", self.run_cli(cli, root, "--version").stdout)
        self.assertEqual(len(hashes), 1)

    def test_upstream_compressed_and_raw_scene_roundtrips(self):
        for skill in SKILLS:
            for raw in (False, True):
                with self.subTest(skill=skill, raw=raw), tempfile.TemporaryDirectory(prefix="siglus-roundtrip-") as tmp:
                    root = Path(tmp)
                    cli = self.isolated_cli(skill, root)
                    inputs = root / "dat"
                    inputs.mkdir()
                    expected = {"chapter01.dat": synthetic_dat(b"synthetic-A" * 20),
                                "chapter02.dat": synthetic_dat(bytes(range(64)))}
                    for name, data in expected.items():
                        (inputs / name).write_bytes(data)
                    original = root / "original.pck"
                    options = ["-c", "--dat-repack", "--no-os"] + (["--no-lzss"] if raw else [])
                    self.run_cli(cli, root, *options, inputs, original)
                    extracted = root / "extracted"
                    self.run_cli(cli, root, "unpack", original, extracted)
                    self.assertEqual({p.name: p.read_bytes() for p in extracted.iterdir()}, expected)
                    rebuilt = root / "rebuilt.pck"
                    self.run_cli(cli, root, "pack", extracted, rebuilt, "--base", original)
                    self.assertEqual(original.read_bytes(), rebuilt.read_bytes())
                    (extracted / "chapter01.dat").write_bytes(synthetic_dat(b"changed synthetic-A" * 30))
                    changed = root / "changed.pck"
                    self.run_cli(cli, root, "pack", extracted, changed, "--base", original)
                    verify = root / "verify"
                    self.run_cli(cli, root, "unpack", changed, verify)
                    self.assertEqual((verify / "chapter01.dat").read_bytes(), (extracted / "chapter01.dat").read_bytes())
                    self.assertEqual((verify / "chapter02.dat").read_bytes(), expected["chapter02.dat"])

    def test_metadata_and_member_identity_survive_changed_lengths(self):
        for skill in SKILLS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory(prefix="siglus-metadata-") as tmp:
                root = Path(tmp)
                cli = self.isolated_cli(skill, root)
                payloads = [synthetic_dat(b"first"), synthetic_dat(b"second")]
                base_bytes, header = synthetic_pck(["First", "第二章"], payloads)
                base = root / "base.pck"
                base.write_bytes(base_bytes)
                inputs = root / "dat"
                self.run_cli(cli, root, "unpack", base, inputs)
                replacement = synthetic_dat(b"synthetic changed payload" * 10)
                (inputs / "First.dat").write_bytes(replacement)
                output = root / "rebuilt.pck"
                self.run_cli(cli, root, "pack", inputs, output, "--base", base)
                actual = output.read_bytes()
                index = header["scn_data_index_list_ofs"]
                data_start = header["scn_data_list_ofs"]
                self.assertEqual(actual[:index], base_bytes[:index])
                self.assertEqual(actual[index + 16:data_start], base_bytes[index + 16:data_start])
                self.assertEqual(struct.unpack_from("<4i", actual, index), (0, len(replacement), len(replacement), len(payloads[1])))
                self.assertEqual(actual[data_start:], replacement + payloads[1])
                # Verify through the independent upstream extraction path as well.
                upstream = root / "upstream"
                result = self.run_cli(cli, root, "-x", output, upstream)
                location = next(line[8:].strip() for line in result.stdout.splitlines() if line.startswith("Output: "))
                self.assertEqual({p.name: p.read_bytes() for p in Path(location).iterdir()},
                                 {"First.dat": replacement, "第二章.dat": payloads[1]})

    def test_embedded_source_is_preserved_and_stale_source_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="siglus-sources-") as tmp:
            root = Path(tmp)
            cli = self.isolated_cli(SKILLS[0], root)
            # Opaque synthetic trailer tests exact retention, not source decryption.
            contents, _ = synthetic_pck(["scene"], [synthetic_dat(b"original")], b"synthetic opaque source trailer")
            base = root / "base.pck"
            base.write_bytes(contents)
            inputs = root / "dat"
            self.run_cli(cli, root, "unpack", base, inputs)
            unmodified = root / "unchanged.pck"
            self.run_cli(cli, root, "pack", inputs, unmodified, "--base", base)
            self.assertEqual(unmodified.read_bytes(), contents)
            (inputs / "scene.dat").write_bytes(synthetic_dat(b"modified"))
            refused = root / "refused.pck"
            self.assertIn("embedded original sources", self.run_cli(cli, root, "pack", inputs, refused, "--base", base, success=False).stderr)
            self.assertFalse(refused.exists())

    def test_project_xor_roundtrip_uses_only_explicit_synthetic_key(self):
        with tempfile.TemporaryDirectory(prefix="siglus-xor-") as tmp:
            root = Path(tmp)
            cli = self.isolated_cli(SKILLS[0], root)
            key = bytes(range(1, 17))
            key_arg = "key=" + ",".join(f"0x{x:02x}" for x in key)
            plain = synthetic_dat(b"synthetic keyed fixture")
            encrypted = bytes(x ^ key[i % len(key)] for i, x in enumerate(plain))
            contents, _ = synthetic_pck(["scene"], [encrypted])
            contents = bytearray(contents)
            struct.pack_into("<i", contents, 84, 1)
            base = root / "base.pck"
            base.write_bytes(contents)
            inputs = root / "dat"
            self.run_cli(cli, root, "unpack", base, inputs, "--angou", key_arg)
            self.assertEqual((inputs / "scene.dat").read_bytes(), plain)
            replacement = synthetic_dat(b"modified synthetic keyed fixture" * 3)
            (inputs / "scene.dat").write_bytes(replacement)
            rebuilt = root / "rebuilt.pck"
            self.run_cli(cli, root, "pack", inputs, rebuilt, "--base", base, "--angou", key_arg)
            verify = root / "verify"
            self.run_cli(cli, root, "unpack", rebuilt, verify, "--angou", key_arg)
            self.assertEqual((verify / "scene.dat").read_bytes(), replacement)

    def test_invalid_names_unknown_layout_and_incomplete_inputs_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="siglus-invalid-") as tmp:
            root = Path(tmp)
            cli = self.isolated_cli(SKILLS[0], root)
            for i, names in enumerate((["../outside"], ["duplicate", "DUPLICATE"])):
                blob, _ = synthetic_pck(names, [synthetic_dat(b"fixture")] * len(names))
                base = root / f"bad{i}.pck"
                base.write_bytes(blob)
                out = root / f"bad{i}"
                self.run_cli(cli, root, "unpack", base, out, success=False)
                self.assertFalse(out.exists())
            blob, _ = synthetic_pck(["scene"], [synthetic_dat(b"fixture")])
            base = root / "base.pck"
            base.write_bytes(blob)
            inputs = root / "empty"
            inputs.mkdir()
            output = root / "missing.pck"
            self.run_cli(cli, root, "pack", inputs, output, "--base", base, success=False)
            self.assertFalse(output.exists())
            unknown = bytearray(blob)
            struct.pack_into("<i", unknown, 0, 96)
            base.write_bytes(unknown)
            self.run_cli(cli, root, "unpack", base, root / "unknown", success=False)

    def test_links_before_and_after_parent_navigation_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="siglus-path-links-") as tmp:
            root = Path(tmp)
            cli = self.isolated_cli(SKILLS[0], root)
            contents, _ = synthetic_pck(["scene"], [synthetic_dat(b"fixture")])
            base = root / "base.pck"
            base.write_bytes(contents)
            dat_dir = root / "dat"
            self.run_cli(cli, root, "unpack", base, dat_dir)
            outside = root / "outside"
            outside.mkdir()
            (outside / "base.pck").write_bytes(contents)
            link = root / "linked"
            self.directory_link(link, outside)
            # The lexical walk must find 'linked' before normalization erases it.
            for output in (link / "new-dir", link / ".." / "escaped"):
                self.assertIn("links and reparse points", self.run_cli(
                    cli, root, "unpack", base, output, success=False).stderr)
            self.run_cli(cli, root, "unpack", link / "base.pck", root / "bad-input", success=False)
            self.run_cli(cli, root, "unpack", link / ".." / "base.pck", root / "bad-dotdot-input", success=False)
            self.run_cli(cli, root, "pack", dat_dir, root / "bad-base.pck", "--base", link / "base.pck", success=False)
            self.run_cli(cli, root, "pack", dat_dir, link / "new.pck", "--base", base, success=False)
            dat_link = root / "dat-link"
            self.directory_link(dat_link, dat_dir)
            self.run_cli(cli, root, "pack", dat_link, root / "bad-root.pck", "--base", base, success=False)
            self.run_cli(cli, root, "pack", link / ".." / "dat", root / "bad-dotdot-root.pck", "--base", base, success=False)
            self.assertEqual({p.name for p in outside.iterdir()}, {"base.pck"})
            self.assertFalse((root / "escaped").exists())
            self.assertFalse((root / "bad-input").exists())
            self.assertFalse((root / "bad-base.pck").exists())
            self.assertFalse((root / "bad-root.pck").exists())
            # Ordinary '..' navigation still works when every component is plain.
            ordinary = root / "ordinary"
            ordinary.mkdir()
            self.run_cli(cli, root, "unpack", ordinary / ".." / "base.pck", root / "ordinary-output")
            archive_link = root / "archive-link.pck"
            self.directory_link(archive_link, outside)
            self.assertIn("links and reparse points", self.run_cli(
                cli, root, "unpack", archive_link, root / "bad-terminal-input", success=False).stderr)
            # A member endpoint must be checked independently of its plain root.
            (dat_dir / "scene.dat").unlink()
            self.directory_link(dat_dir / "scene.dat", outside)
            self.assertIn("links and reparse points", self.run_cli(
                cli, root, "pack", dat_dir, root / "bad-member.pck", "--base", base, success=False).stderr)
            self.assertFalse((root / "bad-member.pck").exists())

    def test_existing_dangling_and_nested_outputs_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="siglus-output-paths-") as tmp:
            root = Path(tmp)
            cli = self.isolated_cli(SKILLS[0], root)
            contents, _ = synthetic_pck(["scene"], [synthetic_dat(b"fixture")])
            base = root / "base.pck"
            base.write_bytes(contents)
            dat_dir = root / "dat"
            self.run_cli(cli, root, "unpack", base, dat_dir)
            existing_dir = root / "existing-dir"
            existing_dir.mkdir()
            (existing_dir / "sentinel").write_bytes(b"keep")
            existing_file = root / "existing.pck"
            existing_file.write_bytes(b"keep file")
            self.run_cli(cli, root, "unpack", base, existing_dir, success=False)
            self.run_cli(cli, root, "unpack", base, existing_file, success=False)
            self.run_cli(cli, root, "pack", dat_dir, existing_file, "--base", base, success=False)
            self.run_cli(cli, root, "pack", dat_dir, existing_dir, "--base", base, success=False)
            self.run_cli(cli, root, "pack", dat_dir, dat_dir / "inside.pck", "--base", base, success=False)
            self.run_cli(cli, root, "pack", dat_dir, root / "ordinary" / ".." / "dat" / "inside.pck", "--base", base, success=False)
            self.assertEqual(existing_file.read_bytes(), b"keep file")
            self.assertEqual((existing_dir / "sentinel").read_bytes(), b"keep")
            self.assertFalse((dat_dir / "inside.pck").exists())
            missing = root / "missing-target"
            missing.mkdir()
            dangling = root / "dangling"
            self.directory_link(dangling, missing)
            missing.rmdir()
            self.assertTrue(os.path.lexists(dangling))
            self.run_cli(cli, root, "unpack", base, dangling, success=False)
            self.run_cli(cli, root, "pack", dat_dir, dangling, "--base", base, success=False)
            self.assertTrue(os.path.lexists(dangling))
            self.assertFalse(missing.exists())

    def test_failed_unpack_does_not_publish_partial_resources(self):
        with tempfile.TemporaryDirectory(prefix="siglus-atomic-unpack-") as tmp:
            root = Path(tmp)
            cli = self.isolated_cli(SKILLS[0], root)
            # The first member can be written; the second exceeds the Windows
            # filename-component limit and forces an actual filesystem failure.
            contents, _ = synthetic_pck(["first", "x" * 260],
                                        [synthetic_dat(b"first"), synthetic_dat(b"second")])
            base = root / "base.pck"
            base.write_bytes(contents)
            output = root / "new-parent" / "nested" / "output"
            self.run_cli(cli, root, "unpack", base, output, success=False)
            self.assertFalse(output.exists())
            self.assertFalse((root / "new-parent").exists())
            self.assertFalse(list(root.rglob(".siglus-unpack-*")))


if __name__ == "__main__":
    unittest.main()
