#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Create a Siglus read copy when the header declares source data but the scenes end at EOF."""

import argparse
import json
import struct
import sys
from pathlib import Path


def prepare(source, output):
    blob = bytearray(source.read_bytes())
    if len(blob) < 92:
        raise ValueError("truncated 92-byte PCK header")
    fields = struct.unpack_from("<23i", blob)
    index, count, base, data_count, transform, source_size = fields[17:]
    if (fields[0] != 92 or transform not in (0, 1) or source_size <= 0
            or not 92 <= index <= base <= len(blob)
            or not 0 < count <= (base - index) // 8 or count != data_count
            or fields[14] != count or fields[16] != count):
        raise ValueError("unsupported scene header or source declaration")
    end = 0
    for offset, length in struct.iter_unpack("<ii", blob[index:index + count * 8]):
        if offset != end or length <= 0 or base + offset + length > len(blob):
            raise ValueError("scene extents must be valid and contiguous")
        end += length
    if base + end != len(blob):
        raise ValueError("file contains bytes after the final scene")
    struct.pack_into("<i", blob, 88, 0)
    created = False
    try:
        with output.open("xb") as destination:
            created = True
            destination.write(blob)
    except OSError:
        if created:
            output.unlink(missing_ok=True)
        raise
    return {"scenes": count, "previous_declared_source_size": source_size,
            "actual_source_tail": 0, "changed_header_offset": 88}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.source, args.output)))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

