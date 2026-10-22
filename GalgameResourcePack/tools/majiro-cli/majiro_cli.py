#!/usr/bin/env python3
"""Bounded flat Majiro ARC V3 CLI; no script or media transformation.

GalSkill adaptation, 2026-10-22, MIT. Upstream notices are in licenses/.
Only canonical CP932 basenames already equal to lower() are supported.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'source/majiro-py/src'))
sys.path.insert(0, str(BASE / 'source'))
from archive_v3 import archive as build_archive
from mjotool.crypt import hash64

MAGIC = b'MajiroArcV3.000\0'
HEADER = struct.Struct('<16sIII')
ENTRY = struct.Struct('<QII')
ENTRY_LIMIT = 100_000
INDEX_LIMIT = 16 * 1024 * 1024
DEFAULT_LIMIT = 256 * 1024 * 1024
DEVICES = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$',
           *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def path_without_links(path):
    raw = path.absolute()
    current = Path(raw.anchor)
    # Inspect before resolving '..', including components it would cancel.
    for part in raw.parts[1:]:
        current = current.parent if part == '..' else current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        require(not (stat.S_ISLNK(info.st_mode) or
                     getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)),
                'Links and reparse points are unsupported')
    return raw.resolve()


def name_bytes(name):
    require(type(name) is str and name and len(name) <= 255,
            'Empty or overlong member name')
    require(name == name.lower(), 'This V3 subset requires names already equal to lower(); no renaming is performed')
    require(not any(ord(c) < 32 or c in '/\\:<>"|?*' for c in name)
            and name not in ('.', '..') and name.rstrip(' .') == name
            and name.split('.')[0].upper() not in DEVICES,
            'Unsafe or unsupported member basename')
    encoded = name.encode('cp932', 'strict')
    require(encoded.decode('cp932', 'strict') == name, 'Member name does not roundtrip in CP932')
    return encoded


def read_index(path, limit):
    length = path.stat().st_size
    require(HEADER.size <= length <= min(limit, 0xFFFFFFFF), 'Archive size exceeds configured/u32 limit or is truncated')
    with path.open('rb') as stream:
        magic, count, names_at, data_at = HEADER.unpack(stream.read(HEADER.size))
        require(magic == MAGIC, 'Only MajiroArcV3.000 is supported; no version conversion is performed')
        require(0 < count <= ENTRY_LIMIT, 'Invalid or excessive member count')
        require(names_at == HEADER.size + count * ENTRY.size and names_at < data_at <= length,
                'Invalid V3 index/name/data boundaries')
        require(data_at - HEADER.size <= INDEX_LIMIT, 'Index exceeds 16 MiB limit')
        table = stream.read(names_at - HEADER.size)
        names = stream.read(data_at - names_at)
    result = []
    seen = set()
    position = 0
    previous_hash = -1
    total = 0
    ranges = []
    for number in range(count):
        end = names.find(b'\0', position)
        require(end > position, 'Missing or empty V3 member name')
        raw_name = names[position:end]
        name = raw_name.decode('cp932', 'strict')
        require(name_bytes(name) == raw_name, 'Noncanonical CP932 name bytes cannot be preserved')
        require(name.casefold() not in seen, 'Duplicate or case-colliding name')
        seen.add(name.casefold())
        position = end + 1
        hashed, offset, size = ENTRY.unpack_from(table, number * ENTRY.size)
        require(hashed > previous_hash, 'V3 hash index must be strictly increasing; collisions are unsupported')
        require(hashed == hash64(raw_name), 'V3 filename hash mismatch for supported lowercase-name convention')
        require(data_at <= offset <= length and size <= length - offset, 'Member lies outside data area')
        previous_hash = hashed
        total += size
        require(total <= limit, 'Total extracted bytes exceed configured limit')
        if size:
            ranges.append((offset, offset + size))
        result.append(dict(name=name, name_hash=f'{hashed:016x}', offset=offset, size=size))
    require(position == len(names), 'Unsupported names padding or extra records')
    previous_end = data_at
    for start, end in sorted(set(ranges)):
        require(start >= previous_end, 'Partially overlapping data ranges are unsupported')
        previous_end = end
    return result


def new_output(path):
    require(not path.exists() and not path.is_symlink(), 'Output must not exist')
    path.parent.mkdir(parents=True, exist_ok=True)


def copy_exact(source, target, size):
    while size:
        block = source.read(min(size, 1024 * 1024))
        require(block, 'Input changed or was truncated during extraction')
        target.write(block)
        size -= len(block)


def extract(source, output, members):
    new_output(output)
    staging = Path(tempfile.mkdtemp(prefix='.majiro-', dir=output.parent))
    try:
        with source.open('rb') as stream:
            for member in members:
                stream.seek(member['offset'])
                with (staging / member['name']).open('xb') as target:
                    copy_exact(stream, target, member['size'])
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def pack(source, output, limit):
    require(source.is_dir(), 'Pack input must be a directory')
    require(not output.is_relative_to(source), 'Output archive must be outside input directory')
    paths = sorted(source.iterdir())
    require(0 < len(paths) <= ENTRY_LIMIT, 'Empty or excessive input member count')
    names = set()
    hashes = set()
    total = HEADER.size + ENTRY.size * len(paths)
    index_size = total - HEADER.size
    sizes = {}
    for path in paths:
        checked = path_without_links(path)
        require(checked.is_file(), 'Flat V3 input accepts ordinary files only; subdirectories are unsupported')
        encoded = name_bytes(path.name)
        require(path.name.casefold() not in names, 'Duplicate or case-colliding input name')
        names.add(path.name.casefold())
        hashed = hash64(encoded)
        require(hashed not in hashes, 'CRC64 filename collision is unsupported')
        hashes.add(hashed)
        sizes[path] = path.stat().st_size
        total += len(encoded) + 1 + sizes[path]
        index_size += len(encoded) + 1
        require(total <= min(limit, 0xFFFFFFFF), 'Archive exceeds configured/u32 size limit')
        require(index_size <= INDEX_LIMIT, 'Index exceeds 16 MiB limit')
    new_output(output)
    files = {}
    for path in paths:
        with path.open('rb') as stream:
            data = stream.read(sizes[path] + 1)
        require(len(data) == sizes[path], 'Input size changed during packing')
        files[path.name] = data
    content = build_archive(files)
    require(len(content) <= min(limit, 0xFFFFFFFF), 'Input changed or output exceeded size limit')
    descriptor, temporary = tempfile.mkstemp(prefix='.majiro-', suffix='.arc', dir=output.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
        read_index(Path(temporary), limit)
        # Atomic publication without replacing a destination created concurrently.
        os.link(temporary, output)
    finally:
        os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='majiro-cli 1.0 / ARC V3 lowercase CP932 subset')
    parser.add_argument('--max-bytes', type=int, default=DEFAULT_LIMIT,
                        help='archive and total output byte limit; default 256 MiB')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('list', 'extract', 'pack'):
        command = commands.add_parser(name)
        command.add_argument('input', type=Path)
        if name != 'list':
            command.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        require(HEADER.size <= args.max_bytes <= 0xFFFFFFFF, '--max-bytes must be between 28 and 4294967295')
        source = path_without_links(args.input)
        if args.command == 'pack':
            output = path_without_links(args.output)
            pack(source, output, args.max_bytes)
            print(json.dumps(dict(output=str(output)), ensure_ascii=True))
        else:
            members = read_index(source, args.max_bytes)
            if args.command == 'list':
                print(json.dumps(dict(version=3, count=len(members), entries=members), ensure_ascii=True))
            else:
                output = path_without_links(args.output)
                extract(source, output, members)
                print(json.dumps(dict(output=str(output)), ensure_ascii=True))
        return 0
    except (OSError, ValueError, OverflowError, struct.error) as error:
        print('majiro-cli: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
