#!/usr/bin/env python3
"""Raw SEEN.TXT archive CLI, adapted from RLdev's archiver.ml.

Copyright (C) 2006 Haeleth (archive layout and original implementation).
GalSkill Python adaptation, 2026. SPDX-License-Identifier: GPL-2.0-or-later.
This tool never decompresses, executes or recompiles scenario bytecode.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import sys
import tempfile

SLOTS = 10000
HEADER_SIZE = SLOTS * 8
NAME = re.compile(r"SEEN([0-9]{4})\.TXT", re.I)


def plain(path):
    original = path.absolute()
    for candidate in (original, *original.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400):
            raise ValueError('Links and reparse points are not supported: ' + str(candidate))


def entries(path, limit):
    plain(path)
    size = path.stat().st_size
    if size > limit or size < HEADER_SIZE:
        raise ValueError('Archive exceeds size limit or lacks the 80000-byte index')
    with path.open('rb') as stream:
        header = stream.read(HEADER_SIZE)
    result = []
    total = 0
    intervals = []
    for slot, (offset, length) in enumerate(struct.iter_unpack('<II', header)):
        if not length:
            continue
        if offset < HEADER_SIZE or offset > size or length > size - offset:
            raise ValueError('Scenario index points outside archive data')
        total += length
        if total > limit:
            raise ValueError('Total extracted size exceeds limit')
        intervals.append((offset, offset + length))
        result.append(dict(slot=slot, path=f'SEEN{slot:04d}.TXT', offset=offset, size=length))
    previous = None
    for interval in sorted(set(intervals)):
        if previous and interval[0] < previous[1]:
            raise ValueError('Partially overlapping scenario entries are unsupported')
        previous = interval
    return result


def copy_bytes(source, target, size):
    while size:
        block = source.read(min(size, 1024 * 1024))
        if not block:
            raise ValueError('Input changed or was truncated while reading')
        target.write(block)
        size -= len(block)


def unpack(source, destination, limit):
    members = entries(source, limit)
    plain(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Output directory must not exist')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.rlseen-', dir=destination.parent))
    try:
        with source.open('rb') as stream:
            for member in members:
                stream.seek(member['offset'])
                with (staging / member['path']).open('xb') as target:
                    copy_bytes(stream, target, member['size'])
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return members


def pack(source, destination, limit):
    plain(source)
    plain(destination)
    if not source.is_dir():
        raise ValueError('Input must be a directory of stored SEENnnnn.TXT members')
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError('Output archive must be outside the input resource directory')
    members = []
    seen = set()
    total = HEADER_SIZE
    for path in source.iterdir():
        plain(path)
        match = NAME.fullmatch(path.name)
        if not path.is_file() or not match:
            raise ValueError('Unexpected member; only immediate SEENnnnn.TXT files are accepted')
        slot = int(match[1])
        if slot in seen:
            raise ValueError('Duplicate scenario number')
        seen.add(slot)
        size = path.stat().st_size
        if not size:
            raise ValueError('Zero-length scenarios cannot be represented as present entries')
        with path.open('rb') as stream:
            if stream.read(4) in (b'KPRL', b'KP2K', b'KPRM', b'RDRL', b'RD2K', b'RDRM'):
                raise ValueError('RLdev uncompressed working scripts must be recompiled/compressed first')
        total += size
        if total > min(limit, 0xffffffff):
            raise ValueError('Archive exceeds configured or 32-bit format size limit')
        members.append((slot, path, size))
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Output archive must not exist')
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.rlseen-', dir=destination.parent)
    try:
        with os.fdopen(fd, 'wb') as target:
            header = bytearray(HEADER_SIZE)
            offset = HEADER_SIZE
            for slot, path, size in sorted(members):
                struct.pack_into('<II', header, slot * 8, offset, size)
                offset += size
            target.write(header)
            for slot, path, size in sorted(members):
                with path.open('rb') as stream:
                    copy_bytes(stream, target, size)
                    if stream.read(1):
                        raise ValueError('Input grew while packing')
        # A hard link publishes without replacing an existing destination.
        os.link(temporary, destination)
    finally:
        os.unlink(temporary)
    return [dict(slot=slot, path=path.name, size=size) for slot, path, size in sorted(members)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='rlseen 1.0 / RLdev 074c8b1')
    parser.add_argument('--max-bytes', type=int, default=1024 * 1024 * 1024,
                        help='maximum archive and total extracted bytes (default 1 GiB)')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('list', 'unpack', 'pack'):
        command = commands.add_parser(name)
        command.add_argument('input', type=Path)
        if name != 'list':
            command.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        if args.max_bytes < HEADER_SIZE:
            raise ValueError('--max-bytes must allow the index header')
        if args.command == 'list':
            result = entries(args.input, args.max_bytes)
        elif args.command == 'unpack':
            result = unpack(args.input, args.output, args.max_bytes)
        else:
            result = pack(args.input, args.output, args.max_bytes)
        print(json.dumps(dict(count=len(result), entries=result), ensure_ascii=True))
        return 0
    except (OSError, ValueError, struct.error) as error:
        print('rlseen: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
