"""Non-interactive ARC20/DSC entry point for bundled skill execution."""
import argparse
import json
import struct
import sys
from pathlib import Path, PurePosixPath

from dsc_compress import write_dsc_file
from dsc_decompress import DscDecoder

MAGIC = b"BURIKO ARC20"
DSC_MAGIC = b"DSC FORMAT 1.00\0"


def entries(path):
    size = path.stat().st_size
    with path.open("rb") as src:
        header = src.read(16)
        if len(header) != 16 or header[:12] != MAGIC:
            raise ValueError("Expected BURIKO ARC20 archive")
        count = struct.unpack_from("<I", header, 12)[0]
        base = 16 + count * 128
        if base > size:
            raise ValueError("Truncated ARC20 index")
        result = []
        seen = set()
        for _ in range(count):
            record = src.read(128)
            name = record[:96].split(b"\0", 1)[0].decode("shift_jis")
            relative = PurePosixPath(name.replace("\\", "/"))
            if (not name or relative.is_absolute() or ".." in relative.parts
                    or any(":" in part for part in relative.parts)):
                raise ValueError(f"Unsafe entry name: {name!r}")
            name = relative.as_posix()
            if name.casefold() in seen:
                raise ValueError(f"Duplicate entry name: {name!r}")
            seen.add(name.casefold())
            offset, length = struct.unpack_from("<II", record, 96)
            if base + offset + length > size:
                raise ValueError(f"Entry outside archive: {name}")
            result.append(dict(name=name, offset=base + offset, size=length))
    return result


def extract(source, target):
    records = entries(source)
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError("Extraction directory must be absent or empty")
    target.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src:
        for item in records:
            output = target / item["name"]
            output.parent.mkdir(parents=True, exist_ok=True)
            src.seek(item["offset"])
            with output.open("xb") as dst:
                remaining = item["size"]
                while remaining:
                    block = src.read(min(remaining, 1024 * 1024))
                    if not block:
                        raise ValueError("Truncated entry payload")
                    dst.write(block)
                    remaining -= len(block)


def create(source, output):
    if not source.is_dir():
        raise ValueError("Create input must be a directory")
    if output.resolve().is_relative_to(source.resolve()):
        raise ValueError("Archive output must be outside input directory")
    paths = sorted((p for p in source.rglob("*") if p.is_file()),
                   key=lambda p: p.relative_to(source).as_posix())
    records = []
    offset = 0
    seen = set()
    for path in paths:
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError(f"Symlink input is unsupported: {path}")
        name = path.relative_to(source).as_posix()
        encoded = name.encode("shift_jis")
        if len(encoded) > 95 or ":" in name or name.casefold() in seen:
            raise ValueError(f"Unsupported or duplicate ARC20 filename: {name}")
        seen.add(name.casefold())
        size = path.stat().st_size
        if offset + size > 0xFFFFFFFF:
            raise ValueError("ARC20 payload exceeds 32-bit offsets")
        records.append(encoded.ljust(96, b"\0") + struct.pack("<II", offset, size) + b"\0" * 24)
        offset += size
    with output.open("xb") as dst:
        dst.write(MAGIC + struct.pack("<I", len(paths)))
        for record in records:
            dst.write(record)
        for path in paths:
            with path.open("rb") as src:
                while block := src.read(1024 * 1024):
                    dst.write(block)


def dsc_metadata(path):
    with path.open("rb") as src:
        header = src.read(32)
    if len(header) != 32 or header[:16] != DSC_MAGIC or path.stat().st_size < 0x220:
        raise ValueError("Expected DSC FORMAT 1.00 stream")
    key, size, count = struct.unpack_from("<III", header, 16)
    return dict(key_hex=f"{key:08X}", original_size=size, symbol_count=count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "dsc-key"):
        commands.add_parser(name).add_argument("input", type=Path)
    for name in ("extract", "create", "dsc-decompress", "dsc-compress"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path)
        command.add_argument("output", type=Path)
        if name == "dsc-compress":
            command.add_argument("key_hex")
    args = parser.parse_args()
    try:
        if args.command == "list":
            print(json.dumps(entries(args.input), ensure_ascii=False))
        elif args.command == "dsc-key":
            print(json.dumps(dsc_metadata(args.input)))
        elif args.command == "extract":
            extract(args.input, args.output)
        else:
            if args.output.exists():
                raise ValueError(f"Output already exists: {args.output}")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.command == "create":
                create(args.input, args.output)
            elif args.command == "dsc-decompress":
                dsc_metadata(args.input)
                data = DscDecoder(args.input.read_bytes()).huffman_decompress()
                with args.output.open("xb") as dst:
                    dst.write(data)
            else:
                key = int(args.key_hex, 16)
                if not 0 <= key <= 0xFFFFFFFF:
                    raise ValueError("DSC key must fit in 32 bits")
                write_dsc_file(args.output, args.input.read_bytes(), key)
        return 0
    except (OSError, ValueError, struct.error, IndexError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
