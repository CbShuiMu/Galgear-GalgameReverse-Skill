"""Decode the ERISA context after the BMP preview in a supported Cotomi slot."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from parse_cotopha_csx import ENTIS, sections


def context_stream(data):
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("expected a BMP-backed slot")
    bitmap_end, = struct.unpack_from("<I", data, 2)
    if not 54 <= bitmap_end <= len(data) - 64:
        raise ValueError("invalid BMP boundary")
    pixels, dib_size = struct.unpack_from("<II", data, 10)
    if dib_size < 12 or not 14 + dib_size <= pixels < bitmap_end:
        raise ValueError("invalid BMP pixel range")
    tail = data[bitmap_end:]
    parts = sections(tail, b"cotomi context file")
    if struct.unpack_from("<Q", tail, 56)[0] != len(tail) - 64 or b"context " not in parts:
        raise ValueError("missing or inconsistent Cotomi context section")
    at, stream = parts[b"context "]
    if len(stream) < 8:
        raise ValueError("truncated ERISA section")
    size, = struct.unpack_from("<I", stream)
    if not 64 <= size <= 64 * 1024 * 1024:
        raise ValueError("unsupported decoded context size")
    return bitmap_end, bitmap_end + at, size, bytes(stream[4:])


def wrap_erisa(data, size):
    name = b"context.bin\0"
    index_size = 4 + 40 + len(name)
    entry = struct.pack("<QIIqQII", size, 0, 0x80000010, 16 + index_size, 0, 0, len(name)) + name
    header = (ENTIS + struct.pack("<II", 0x02000400, 0) + b"ERISA-Archive file").ljust(64, b"\0")
    return header + struct.pack("<8sQI", b"DirEntry", index_size, 1) + entry + struct.pack(
        "<8sQ", b"filedata", len(data) + 4
    ) + data + b"\0" * 4


def inspect(path, backend):
    data = path.read_bytes()
    bitmap_end, context_offset, size, encoded = context_stream(data)
    with tempfile.TemporaryDirectory(prefix="cotomi-") as work:
        archive = Path(work) / "context.noa"
        output = Path(work) / "out"
        archive.write_bytes(wrap_erisa(encoded, size))
        result = subprocess.run([str(backend.resolve()), str(archive), str(output), "NOA"],
                                capture_output=True, timeout=30)
        if result.returncode:
            raise ValueError("GARbro could not decode the ERISA member")
        decoded = (output / "00000000.bin").read_bytes()
    if len(decoded) != size:
        raise ValueError("decoded context length differs")
    parts = sections(decoded, b"Cotopha Script Context")
    inner = parts.get(b"context ")
    if (struct.unpack_from("<Q", decoded, 56)[0] != len(decoded) - 64 or inner is None
            or len(inner[1]) < 4 or not {b"classvec", b"global  ", b"stack   ", b"heap    "} <= parts.keys()):
        raise ValueError("missing or inconsistent decoded context sections")
    return {
        "slot_sha256": hashlib.sha256(data).hexdigest(), "bmp_end": bitmap_end, "context_offset": context_offset,
        "decoded_size": size, "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        "sections": {k.decode("ascii").rstrip(): [at, len(v)] for k, (at, v) in parts.items()},
        "context_first_u32": struct.unpack_from("<I", inner[1])[0],
    }, decoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slot", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoded", type=Path)
    parser.add_argument("--backend", type=Path, default=Path(__file__).resolve().parents[1]
                        / "tools/GARbro-cli/GalArchiveExport.exe")
    args = parser.parse_args()
    try:
        report, decoded = inspect(args.slot, args.backend)
        with args.output.open("x", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
        if args.decoded:
            with args.decoded.open("xb") as f:
                f.write(decoded)
    except (OSError, ValueError, struct.error, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
