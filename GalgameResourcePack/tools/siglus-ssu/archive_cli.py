"""Conservative Scene.pck baseline adapter for pinned siglus-ssu 0.5.7.

The upstream CLI remains available with its original option names. This adapter
only rewrites existing scene payloads; it does not regenerate package metadata.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile

from siglus_ssu import const as C
from siglus_ssu import dat, pck
from siglus_ssu.native_ops import lzss_pack, lzss_unpack, xor_cycle_inplace


def _lstat_plain(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"links and reparse points are not allowed: {path}")
    return info


def _walk_plain(path):
    """Check the lexical path before any '..' or link normalization."""
    path = Path(path)
    if path.drive and not path.root:
        raise ValueError("drive-relative paths are not supported")
    if str(path).startswith(("\\\\?\\", "\\\\.\\")):
        raise ValueError("Windows device namespace paths are not supported")
    if not path.is_absolute():
        path = Path.cwd() / path
    current = Path(path.anchor)
    _lstat_plain(current)
    for i, part in enumerate(path.parts[1:]):
        current = current / part
        info = _lstat_plain(current)
        if info is not None and i < len(path.parts) - 2 and not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"path parent is not a directory: {current}")
    return path


def _checked_path(path, kind=None, new=False):
    lexical = _walk_plain(path)
    normalized = lexical.resolve(strict=False)
    _walk_plain(lexical)
    _walk_plain(normalized)
    info = _lstat_plain(normalized)
    if new and info is not None:
        raise ValueError("output already exists; select a new path")
    if kind == "file" and (info is None or not stat.S_ISREG(info.st_mode)):
        raise ValueError(f"input is not an ordinary file: {normalized}")
    if kind == "directory" and (info is None or not stat.S_ISDIR(info.st_mode)):
        raise ValueError(f"input is not an ordinary directory: {normalized}")
    return normalized


def _prepare_parent(path):
    """Create only validated ordinary parents; return those owned by this call."""
    parent = _checked_path(path.parent)
    missing, current = [], parent
    while _lstat_plain(current) is None:
        missing.append(current)
        current = current.parent
    _checked_path(current, kind="directory")
    created = []
    try:
        for item in reversed(missing):
            _checked_path(item, new=True)
            item.mkdir()
            created.append(item)
        _checked_path(parent, kind="directory")
        return created
    except BaseException:
        _cleanup_parents(created)
        raise


def _cleanup_parents(created):
    for parent in reversed(created):
        try:
            _checked_path(parent, kind="directory").rmdir()
        except (OSError, ValueError):
            pass


def _publish_stage(stage, destination, lexical_output):
    # Windows rename is atomic on the same volume and refuses an existing
    # destination. POSIX directory rename may replace an empty directory.
    if os.name != "nt":
        raise ValueError("atomic archive publication requires Windows")
    _checked_path(lexical_output, new=True)
    _checked_path(destination, new=True)
    _checked_path(stage)
    os.rename(stage, destination)


def _cleanup_stage(stage, parent):
    if stage is None:
        return
    checked = _checked_path(stage)
    if checked.parent != parent:
        raise ValueError("temporary output escaped its parent")
    info = _lstat_plain(checked)
    if info is None:
        return
    if stat.S_ISDIR(info.st_mode):
        shutil.rmtree(checked)
    else:
        checked.unlink()


def _pairs(blob, offset, count, limit):
    if count < 0 or offset < 0 or offset > limit or count > (limit - offset) // 8:
        raise ValueError("index is outside metadata")
    if count and offset < C.PACK_HDR_SIZE:
        raise ValueError("index overlaps header")
    return [struct.unpack_from("<ii", blob, offset + i * 8) for i in range(count)]


def _names(blob, index, base, limit):
    result = []
    for offset, length in index:
        if base < C.PACK_HDR_SIZE or offset < 0 or length < 0:
            raise ValueError("invalid name offset/length")
        start, end = base + offset * 2, base + (offset + length) * 2
        if start > limit or end > limit:
            raise ValueError("name is outside metadata")
        result.append(blob[start:end].decode("utf-16le"))
    return result


def _layout(blob):
    if len(blob) < C.PACK_HDR_SIZE:
        raise ValueError("truncated PCK header")
    h = dict(zip(C.PACK_HDR_FIELDS, struct.unpack_from("<23i", blob)))
    if h["header_size"] != 92 or h["scn_data_exe_angou_mod"] not in (0, 1):
        raise ValueError("unsupported PCK header/version")
    base = h["scn_data_list_ofs"]
    if not 92 <= base <= len(blob):
        raise ValueError("invalid scene data base")
    n = h["scn_data_cnt"]
    if n <= 0 or any(h[key] != n for key in (
        "scn_data_index_cnt", "scn_name_cnt", "scn_name_index_cnt"
    )):
        raise ValueError("scene name/data counts disagree")
    occupied = []
    for prefix in ("inc_prop", "inc_cmd", "scn"):
        if prefix == "scn":
            index_key, count_key, name_key = "scn_name_index_list_ofs", "scn_name_index_cnt", "scn_name_cnt"
        else:
            index_key, count_key, name_key = prefix + "_name_index_list_ofs", prefix + "_name_index_cnt", prefix + "_name_cnt"
        count = h[count_key]
        if count != h[name_key] or (prefix != "scn" and count != h[prefix + "_cnt"]):
            raise ValueError("package metadata counts disagree")
        idx = _pairs(blob, h[index_key], count, base)
        _names(blob, idx, h[prefix + "_name_list_ofs"], base)
        if count:
            occupied.append((h[index_key], h[index_key] + count * 8))
            for offset, length in idx:
                start = h[prefix + "_name_list_ofs"] + offset * 2
                occupied.append((start, start + length * 2))
        if prefix != "scn":
            _pairs(blob, h[prefix + "_list_ofs"], h[prefix + "_cnt"], base)
            if count:
                occupied.append((h[prefix + "_list_ofs"], h[prefix + "_list_ofs"] + count * 8))
    name_idx = _pairs(blob, h["scn_name_index_list_ofs"], n, base)
    names = _names(blob, name_idx, h["scn_name_list_ofs"], base)
    seen = set()
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    for name in names:
        if (not name or any(c in name for c in '\\/:*?"<>|\x00')
                or any(ord(c) < 32 for c in name) or name.endswith((" ", "."))
                or name.split(".", 1)[0].casefold() in reserved
                or name.casefold() in seen):
            raise ValueError("unsupported or duplicate scene filename")
        seen.add(name.casefold())
    index_ofs = h["scn_data_index_list_ofs"]
    indices = _pairs(blob, index_ofs, n, base)
    index_end = index_ofs + n * 8
    if any(a < index_end and index_ofs < b for a, b in occupied):
        raise ValueError("scene index overlaps other metadata")
    end = 0
    payloads = []
    for offset, length in indices:
        if offset != end or length <= 0 or base + offset + length > len(blob):
            raise ValueError("unsupported noncontiguous or invalid scene data")
        payloads.append(blob[base + offset:base + offset + length])
        end += length
    tail_start = base + end
    source_size = h["original_source_header_size"]
    if source_size < 0 or source_size > len(blob) - tail_start:
        raise ValueError("invalid embedded source header")
    if tail_start != len(blob) and source_size == 0:
        raise ValueError("unknown trailing PCK data")
    return h, names, payloads, tail_start


def _xor(blob, key):
    result = bytearray(blob)
    xor_cycle_inplace(result, key, 0)
    return bytes(result)


def _decode(payload, key):
    raw = _xor(payload, key) if key else payload
    if dat.scn_structure_valid(raw):
        return raw, "raw"
    if pck.looks_like_lzss(raw):
        plain, mode = lzss_unpack(raw), "lzss"
    else:
        unmasked = _xor(raw, C.EASY_ANGOU_CODE)
        if not pck.looks_like_lzss(unmasked):
            raise ValueError("unsupported scene payload transform")
        plain, mode = lzss_unpack(unmasked), "easy-lzss"
    if not dat.scn_structure_valid(plain):
        raise ValueError("decoded DAT has invalid section bounds")
    return plain, mode


def _open_base(path, angou):
    path = _checked_path(path, kind="file")
    if angou and not angou.startswith(("key=", "angou=")):
        angou = str(_checked_path(angou))
    blob = path.read_bytes()
    h, names, payloads, tail_start = _layout(blob)
    key = pck.require_pck_scene_exe_el(
        blob, input_pck=str(path), hdr=h, scn_data=payloads,
        explicit_angou=angou, source_entries=[]
    )
    scenes = [_decode(payload, key) for payload in payloads]
    return blob, h, names, payloads, tail_start, key, scenes


def _unpack(args):
    destination = _checked_path(args.output, new=True)
    blob, h, names, payloads, tail_start, key, scenes = _open_base(args.archive, args.angou)
    created = _prepare_parent(destination)
    stage, published = None, False
    try:
        _checked_path(args.output, new=True)
        stage = Path(tempfile.mkdtemp(prefix=".siglus-unpack-", dir=destination.parent))
        _checked_path(stage, kind="directory")
        for name, (plain, mode) in zip(names, scenes):
            member = _checked_path(stage / (name + ".dat"), new=True)
            with member.open("xb") as output:
                output.write(plain)
        _publish_stage(stage, destination, args.output)
        published = True
    finally:
        _cleanup_stage(stage, destination.parent)
        if not published:
            _cleanup_parents(created)
    print(json.dumps({"output": str(destination), "scenes": len(names),
                      "embedded_source_retained_in_base": bool(h["original_source_header_size"])}, ensure_ascii=False))
    return 0


def _pack(args):
    destination = _checked_path(args.output, new=True)
    input_root = _checked_path(args.input, kind="directory")
    if destination.is_relative_to(input_root):
        raise ValueError("output archive must be outside the DAT directory")
    blob, h, names, payloads, tail_start, key, scenes = _open_base(args.base, args.angou)
    files = [_checked_path(p, kind="file") for p in input_root.iterdir()]
    expected = {name + ".dat" for name in names}
    if {p.name for p in files} != expected:
        raise ValueError("DAT names must exactly match every scene in the base PCK")
    replacements = [_checked_path(input_root / (name + ".dat"), kind="file").read_bytes() for name in names]
    if not all(dat.scn_structure_valid(value) for value in replacements):
        raise ValueError("replacement DAT has invalid section bounds")
    changed = sum(value != old[0] for value, old in zip(replacements, scenes))
    if changed and h["original_source_header_size"]:
        raise ValueError("modified DAT would disagree with embedded original sources; unsupported")
    prefix = bytearray(blob[:h["scn_data_list_ofs"]])
    result_payloads, offset = [], 0
    for i, (value, old, payload) in enumerate(zip(replacements, scenes, payloads)):
        if value == old[0]:
            encoded = payload
        else:
            mode = old[1]
            encoded = value if mode == "raw" else lzss_pack(value)
            if mode == "easy-lzss":
                encoded = _xor(encoded, C.EASY_ANGOU_CODE)
            if key:
                encoded = _xor(encoded, key)
        if offset > 0x7fffffff or len(encoded) > 0x7fffffff - offset:
            raise ValueError("scene data exceeds signed 32-bit index limits")
        struct.pack_into("<ii", prefix, h["scn_data_index_list_ofs"] + i * 8, offset, len(encoded))
        offset += len(encoded)
        result_payloads.append(encoded)
    output = bytes(prefix) + b"".join(result_payloads) + blob[tail_start:]
    oh, onames, opayloads, _ = _layout(output)
    if onames != names or [_decode(p, key)[0] for p in opayloads] != replacements:
        raise ValueError("post-build scene verification failed")
    created = _prepare_parent(destination)
    stage, published = None, False
    try:
        _checked_path(args.output, new=True)
        fd, temporary = tempfile.mkstemp(prefix=".siglus-pack-", dir=destination.parent)
        stage = Path(temporary)
        with os.fdopen(fd, "wb") as target:
            target.write(output)
            target.flush()
            os.fsync(target.fileno())
        _publish_stage(stage, destination, args.output)
        published = True
    finally:
        _cleanup_stage(stage, destination.parent)
        if not published:
            _cleanup_parents(created)
    print(json.dumps({"output": str(destination), "scenes": len(names),
                      "changed": changed, "sha256": hashlib.sha256(output).hexdigest()}, ensure_ascii=False))
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("pack", "unpack", "--help", "-h"):
        from siglus_ssu.__main__ import main as upstream_main
        return upstream_main()
    parser = argparse.ArgumentParser(description="Siglus scene archive adapter / siglus-ssu 0.5.7. Upstream options remain available (for example -x or -c).")
    sub = parser.add_subparsers(dest="command", required=True)
    unpack = sub.add_parser("unpack", help="extract decoded scene DAT files; retain original PCK as baseline")
    unpack.add_argument("archive", type=Path)
    unpack.add_argument("output", type=Path)
    pack = sub.add_parser("pack", help="replace scene DAT files while preserving package metadata from --base")
    pack.add_argument("input", type=Path)
    pack.add_argument("output", type=Path)
    pack.add_argument("--base", type=Path, required=True)
    for child in (unpack, pack):
        child.add_argument("--angou", default="", help="explicit upstream key source; keep project keys local")
    args = parser.parse_args()
    try:
        return _unpack(args) if args.command == "unpack" else _pack(args)
    except (OSError, ValueError, RuntimeError, struct.error, UnicodeError) as exc:
        print(f"siglus-ssu: {exc}", file=sys.stderr)
        return 1
