"""Read a PKP v0 archive with strict UTF-16LE index and raw DEFLATE members."""
import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

HEADER = struct.Struct("<4sII")
RECORD = struct.Struct("<III36s128s")


def read_index(stream):
    stream.seek(0, 2)
    total = stream.tell()
    stream.seek(0)
    magic, version, count = HEADER.unpack(stream.read(HEADER.size))
    if magic != b"PKP\0" or version != 0 or not 0 < count <= (total - HEADER.size) // RECORD.size:
        raise ValueError("unsupported PKP header or directory size")
    end = HEADER.size + count * RECORD.size
    entries = []
    for ordinal in range(count):
        offset, expanded, stored, reserved, name_field = RECORD.unpack(stream.read(RECORD.size))
        if any(reserved) or offset != end or not 0 < stored <= total - offset or expanded == 0:
            raise ValueError(f"invalid layout at member {ordinal}")
        name = name_field.decode("utf-16le").split("\0", 1)
        if len(name) != 2 or not name[0] or name[1].strip("\0"):
            raise ValueError(f"invalid filename field at member {ordinal}")
        entries.append({"entry": ordinal, "name": name[0], "offset": offset,
                        "stored_size": stored, "logical_size": expanded})
        end = offset + stored
    if end != total:
        raise ValueError("payload range does not end at EOF")
    return entries


def extract_member(source, out, entry, stored_only):
    source.seek(entry["offset"])
    remaining = entry["stored_size"]
    limit = entry["logical_size"]
    decoder = None if stored_only else zlib.decompressobj(-zlib.MAX_WBITS)
    digest = hashlib.sha256()
    size = 0
    while remaining:
        data = source.read(min(remaining, 32768))
        if not data:
            raise ValueError("truncated payload")
        remaining -= len(data)
        if decoder is not None:
            data = decoder.decompress(data, min(limit - size + 1, 64 << 20))
            if (size + len(data) > limit or decoder.unused_data or decoder.unconsumed_tail
                    or (remaining and decoder.eof)):
                raise ValueError("raw DEFLATE exceeds its indexed size or has trailing data")
        out.write(data)
        digest.update(data)
        size += len(data)
    if decoder is not None and (size != limit or not decoder.eof):
        raise ValueError("raw DEFLATE size or stream terminator differs from index")
    return size, digest.hexdigest()


def extract(source, entries, output, stored_only):
    output.mkdir()
    failed = 0
    with (output / "manifest.jsonl").open("x", encoding="utf-8") as manifest:
        for entry in entries:
            filename = f"{entry['entry']:06d}.bin"
            target = output / filename
            temporary = target.with_suffix(".partial")
            try:
                with temporary.open("xb") as out:
                    size, digest = extract_member(source, out, entry, stored_only)
                temporary.rename(target)
                result = {"status": "ok", "file": filename, "size": size, "sha256": digest}
            except (OSError, ValueError, zlib.error) as exc:
                temporary.unlink(missing_ok=True)
                failed += 1
                result = {"status": "error", "error": str(exc)}
            manifest.write(json.dumps({**entry, **result,
                                       "layer": "stored" if stored_only else "logical"}) + "\n")
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    commands.add_parser("list").add_argument("archive", type=Path)
    unpack = commands.add_parser("extract")
    unpack.add_argument("archive", type=Path)
    unpack.add_argument("output", type=Path)
    unpack.add_argument("--stored", action="store_true")
    args = parser.parse_args()
    try:
        with args.archive.open("rb") as source:
            entries = read_index(source)
            if args.mode == "list":
                print(json.dumps(entries))
                return 0
            failed = extract(source, entries, args.output, args.stored)
        print(json.dumps({"listed": len(entries), "failed": failed}))
        return int(bool(failed))
    except (ValueError, OSError, struct.error) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

