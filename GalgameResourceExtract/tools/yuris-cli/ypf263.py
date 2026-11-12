#!/usr/bin/env python3
"""Read standalone YU-RIS YPF 263 archives with Adler-32 index and payload checks."""

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path


# Version 263 uses the legacy permutation (GARbro ArcYPF.cs SwapTable04).
LENGTHS = list(range(256))
for left, right in ((12, 16), (17, 25), (28, 30), (9, 11), (13, 19), (21, 27), (32, 35), (38, 41), (44, 47), (46, 50)):
    LENGTHS[left], LENGTHS[right] = right, left


def read_exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("truncated archive")
    return data


def read_index(stream):
    stream.seek(0, 2)
    archive_size = stream.tell()
    stream.seek(0)
    magic, version, count, size = struct.unpack("<4sIII16x", read_exact(stream, 32))
    if magic != b"YPF\0" or version != 263:
        raise ValueError("expected standalone YPF version 263")
    if not 0 < count <= 1_000_000 or not count * 24 <= size <= count * 278 or size + 32 > archive_size:
        raise ValueError("invalid YPF index size or count")
    data = read_exact(stream, size)
    raw_entries = []
    position = 0
    for entry in range(count):
        if position + 5 > size:
            raise ValueError(f"truncated index at entry {entry}")
        name_adler, length = struct.unpack_from("<IB", data, position)
        length = LENGTHS[length ^ 0xFF]
        name_start = position + 5
        name_end = name_start + length
        position = name_end + 18
        if not length or position > size:
            raise ValueError(f"truncated or empty name at entry {entry}")
        kind, packed, unpacked, stored, offset, payload_adler = struct.unpack_from("<BBIIII", data, name_end)
        if (packed not in (0, 1) or (not packed and stored != unpacked)
                or offset < size + 32 or offset + stored > archive_size):
            raise ValueError(f"invalid payload extent at entry {entry}")
        raw_entries.append((data[name_start:name_end], name_adler, kind, packed, unpacked,
                            stored, offset, payload_adler))
    if position != size:
        raise ValueError("index length does not match its entries")

    keys = set(range(256))
    rows = []
    for raw, name_adler, *_ in raw_entries:
        keys = {key for key in keys if zlib.adler32(bytes(byte ^ key for byte in raw)) == name_adler}
        if not keys:
            raise ValueError("no filename transform matches all Adler-32 values")
    if len(keys) != 1:
        raise ValueError("filename transform is ambiguous")
    key = keys.pop()
    for entry, (raw, checksum, kind, packed, unpacked, stored, offset, payload_adler) in enumerate(raw_entries):
        plain = bytes(byte ^ key for byte in raw)
        try:
            name = plain.decode("cp932", errors="strict")
        except UnicodeDecodeError:
            name = None
        rows.append({"entry": entry, "name": name, "name_hex": plain.hex(), "name_adler32": checksum,
                     "kind": kind, "packed": bool(packed), "decoded_size": unpacked,
                     "stored_size": stored, "offset": offset, "payload_adler32": payload_adler})
    return rows


def copy_payload(source, output, row, stored_only):
    source.seek(row["offset"])
    remaining = row["stored_size"]
    declared = row["decoded_size"]
    decoder = zlib.decompressobj() if row["packed"] and not stored_only else None
    checksum = 1
    digest = hashlib.sha256()
    written = 0
    while remaining:
        data = read_exact(source, min(remaining, 65536))
        remaining -= len(data)
        checksum = zlib.adler32(data, checksum)
        if decoder is not None:
            data = decoder.decompress(data, min(declared - written + 1, 64 << 20))
            if (written + len(data) > declared or decoder.unconsumed_tail
                    or decoder.unused_data or (decoder.eof and remaining)):
                raise ValueError("member zlib stream exceeds declared size or contains trailing bytes")
        output.write(data)
        written += len(data)
        digest.update(data)
    if checksum != row["payload_adler32"]:
        raise ValueError("stored payload Adler-32 mismatch")
    if decoder is not None and (not decoder.eof or written != declared):
        raise ValueError("incomplete zlib stream or mismatched decoded length")
    return written, digest.hexdigest()


def extract(source, rows, output, stored_only):
    output.mkdir()
    failures = 0
    with (output / "manifest.jsonl").open("x", encoding="utf-8") as manifest:
        for row in rows:
            filename = f"{row['entry']:08d}.bin"
            target = output / filename
            temporary = target.with_suffix(".partial")
            try:
                with temporary.open("xb") as stream:
                    size, digest = copy_payload(source, stream, row, stored_only)
                temporary.rename(target)
                result = {"status": "ok", "file": filename, "size": size, "sha256": digest}
            except (OSError, ValueError, zlib.error) as exc:
                temporary.unlink(missing_ok=True)
                result = {"status": "error", "error": str(exc)}
                failures += 1
            manifest.write(json.dumps({**row, **result,
                                       "layer": "stored" if stored_only else "logical"},
                                      ensure_ascii=True) + "\n")
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list").add_argument("archive", type=Path)
    unpack = commands.add_parser("extract")
    unpack.add_argument("archive", type=Path)
    unpack.add_argument("output", type=Path)
    unpack.add_argument("--stored", action="store_true", help="keep stored payloads without zlib decoding")
    args = parser.parse_args(argv)
    try:
        with args.archive.open("rb") as source:
            rows = read_index(source)
            if args.command == "list":
                print(json.dumps(rows, ensure_ascii=True))
                return 0
            failures = extract(source, rows, args.output, args.stored)
        if failures:
            print(f"{failures} of {len(rows)} members failed; see manifest.jsonl", file=sys.stderr)
            return 1
        print(f"{len(rows)} members extracted")
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

