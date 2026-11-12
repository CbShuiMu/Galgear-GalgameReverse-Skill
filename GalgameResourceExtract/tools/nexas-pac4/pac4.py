#!/usr/bin/env python3
"""List or extract NeXAS type-4 PAC archives with an inverted Huffman footer."""

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path


def huffman_index(packed, length, allow_short_tail=False):
    # The serialized tree is preorder: 0 + eight symbol bits, or 1 + two children.
    bits = ((byte >> shift) & 1 for byte in packed for shift in range(7, -1, -1))
    branches = 0

    def tree():
        nonlocal branches
        if next(bits):
            branches += 1
            if branches > 255:
                raise ValueError("Huffman tree has too many branches")
            return tree(), tree()
        value = 0
        for _ in range(8):
            value = (value << 1) | next(bits)
        return value

    try:
        root = tree()
    except StopIteration as exc:
        raise ValueError("truncated Huffman tree") from exc
    output = bytearray(length)
    try:
        for i in range(length):
            node = root
            while isinstance(node, tuple):
                node = node[next(bits)]
            output[i] = node
    except StopIteration as exc:
        if allow_short_tail and 1 <= length - i <= 3:
            return output, length - i
        raise ValueError("truncated Huffman index") from exc
    return output, 0


def read_exact(stream, length):
    data = stream.read(length)
    if len(data) != length:
        raise ValueError("truncated archive")
    return data


def read_index(stream, encoding, recover_tail=False):
    stream.seek(0, 2)
    total = stream.tell()
    if total < 17:
        raise ValueError("archive header or footer is truncated")
    stream.seek(0)
    magic, count, method = struct.unpack("<4sII", read_exact(stream, 12))
    if magic[:3] != b"PAC" or method != 4 or not 0 < count <= 1_000_000:
        raise ValueError("expected NeXAS PAC with type-4 payloads")
    stream.seek(-4, 2)
    packed, = struct.unpack("<I", read_exact(stream, 4))
    index_start = total - packed - 4
    index_size = count * 76
    if not 0 < packed <= index_size * 2 or index_start < 12:
        raise ValueError("footer index extent is out of bounds")
    stream.seek(index_start)
    encoded = bytes(value ^ 0xFF for value in read_exact(stream, packed))
    index, missing = huffman_index(encoded, index_size, recover_tail)
    rows = []
    for ordinal, (raw_name, offset, decoded, stored) in enumerate(struct.iter_unpack("<64sIII", index)):
        recovered = missing != 0 and ordinal == count - 1
        if recovered:
            available = index_start - offset
            known_mask = (1 << (8 * (4 - missing))) - 1
            previous_end = max((r["offset"] + r["stored_size"] for r in rows), default=12)
            if previous_end != offset or not 0 < available <= 0xFFFFFFFF or available & known_mask != stored:
                raise ValueError("truncated last size does not agree with the contiguous payload extent")
            stored = available
        raw_name, separator, _ = raw_name.partition(b"\0")
        if not separator or not raw_name or offset < 12 or offset + stored > index_start:
            raise ValueError(f"invalid index row {ordinal}")
        try:
            name = raw_name.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            name = None
        rows.append({"entry": ordinal, "name": name, "name_hex": raw_name.hex(),
                     "offset": offset, "stored_size": stored, "decoded_size": decoded,
                     "tail_size_inferred": recovered})
    return rows


def copy_payload(source, output, entry, stored_only):
    source.seek(entry["offset"])
    remaining = entry["stored_size"]
    declared = entry["decoded_size"]
    decode = not stored_only and remaining != declared
    decoder = zlib.decompressobj() if decode else None
    sha256 = hashlib.sha256()
    written = 0
    while remaining:
        block = read_exact(source, min(remaining, 1 << 16))
        remaining -= len(block)
        if decoder is not None:
            block = decoder.decompress(block, min(declared - written + 1, 64 << 20))
            if (written + len(block) > declared or decoder.unconsumed_tail
                    or decoder.unused_data or (decoder.eof and remaining)):
                raise ValueError("zlib stream exceeds declared size or has trailing bytes")
        sha256.update(block)
        output.write(block)
        written += len(block)
    if decoder is not None and (not decoder.eof or written != declared):
        raise ValueError("zlib stream is incomplete or decoded length differs")
    return written, sha256.hexdigest()


def extract(source, rows, destination, stored_only):
    destination.mkdir()
    failures = 0
    with (destination / "manifest.jsonl").open("x", encoding="utf-8") as manifest:
        for entry in rows:
            filename = f"{entry['entry']:08d}.bin"
            target = destination / filename
            temporary = target.with_suffix(".partial")
            try:
                with temporary.open("xb") as out:
                    size, checksum = copy_payload(source, out, entry, stored_only)
                temporary.rename(target)
                outcome = {"status": "ok", "file": filename, "size": size, "sha256": checksum}
            except (OSError, ValueError, zlib.error) as exc:
                temporary.unlink(missing_ok=True)
                outcome = {"status": "error", "error": str(exc)}
                failures += 1
            manifest.write(json.dumps({**entry, **outcome,
                                       "layer": "stored" if stored_only else "logical"},
                                      ensure_ascii=True) + "\n")
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", choices=("cp932", "gbk", "utf-8"), default="cp932",
                        help="decode displayed names only; original index bytes are kept")
    parser.add_argument("--recover-tail", action="store_true",
                        help="infer a short final size field only from matching contiguous extents")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list").add_argument("archive", type=Path)
    unpack = commands.add_parser("extract")
    unpack.add_argument("archive", type=Path)
    unpack.add_argument("output", type=Path)
    unpack.add_argument("--entry", type=int, action="append", help="zero-based entry ID (repeatable)")
    unpack.add_argument("--stored", action="store_true", help="copy original extents without decoding")
    args = parser.parse_args(argv)

    try:
        with args.archive.open("rb") as source:
            rows = read_index(source, args.encoding, args.recover_tail)
            if args.command == "list":
                print(json.dumps(rows, ensure_ascii=True))
                return 0
            if args.entry:
                wanted = set(args.entry)
                if any(i < 0 or i >= len(rows) for i in wanted):
                    raise ValueError("entry ID out of range")
                rows = [row for row in rows if row["entry"] in wanted]
            failed = extract(source, rows, args.output, args.stored)
            if failed:
                print(f"{failed} of {len(rows)} members failed; see manifest.jsonl", file=sys.stderr)
                return 1
            print(f"{len(rows)} members extracted")
            return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

