"""Majiro V3 writer excerpt adapted from NarciBloom's archive(files).

Copyright (c) 2026 RepressedAlliance. MIT; see licenses/NarciBloom-MIT.txt.
Source: tools/patch_narcissu_font.py at
68b1771df55896cb738c5693e2ba861557af8ca2.
GalSkill adaptation: remove project paths and font/patch integration, expose
the function with bundled hash dependency; validation is performed by the CLI.
Only names already equal to lower() are passed, so no names are normalized.
"""
import struct
from mjotool.crypt import hash64


def archive(files):
    ordered = sorted((hash64(name.lower()), name.encode('cp932'), data)
                     for name, data in files.items())
    names = b''.join(name + b'\0' for _, name, _ in ordered)
    names_start = 28 + 16 * len(ordered)
    data_start = names_start + len(names)
    header = struct.pack('<16sIII', b'MajiroArcV3.000\0', len(ordered), names_start, data_start)
    table = bytearray()
    payload = bytearray()
    for hashed, name, data in ordered:
        table.extend(struct.pack('<QII', hashed, data_start + len(payload), len(data)))
        payload.extend(data)
    return header + table + names + payload
