#!/usr/bin/env python3
"""Bounded RPA v2/v3 CLI; preserve the adjacent upstream rpatool unchanged."""

from __future__ import annotations

import argparse
import io
import ntpath
import os
from pathlib import Path
import pickle
import pickletools
import runpy
import stat
import sys
import tempfile
import zlib

MIB = 1024 * 1024
INDEX_LIMIT = 64 * MIB
ENTRY_LIMIT = 100_000
CHUNK_LIMIT = 1_000_000
FORBIDDEN_OPS = {
    "GLOBAL", "STACK_GLOBAL", "REDUCE", "BUILD", "INST", "OBJ", "NEWOBJ",
    "NEWOBJ_EX", "EXT1", "EXT2", "EXT4", "PERSID", "BINPERSID",
}


class DataError(ValueError):
    pass


class DataUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise DataError("pickle globals are not supported")

    def persistent_load(self, pid):
        raise DataError("pickle persistent objects are not supported")


def read_pickle(data):
    stop = -1
    for count, (op, _arg, position) in enumerate(pickletools.genops(data), 1):
        if count > 2_000_000 or op.name in FORBIDDEN_OPS:
            raise DataError("unsupported or excessive pickle instructions")
        if op.name == "STOP":
            stop = position
    if stop != len(data) - 1:
        raise DataError("trailing pickle data")
    stream = io.BytesIO(data)
    value = DataUnpickler(stream, encoding="bytes").load()
    if stream.read(1):
        raise DataError("trailing pickle data")
    return value


def member_name(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", "strict")
    if type(value) is not str or not value or "\0" in value:
        raise DataError("invalid archive member name")
    value = value.replace("\\", "/")
    if ntpath.splitdrive(value)[0] or value.startswith("/"):
        raise DataError("absolute archive member path")
    parts = value.split("/")
    for part in parts:
        if (not part or part in (".", "..") or part.rstrip(" .") != part
                or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                or part.split(".")[0].upper() in {
                    "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
                    *(f"COM{i}" for i in range(1, 10)),
                    *(f"LPT{i}" for i in range(1, 10)),
                }):
            raise DataError("unsafe archive member path")
    return value


def validate_names(names):
    seen = set()
    result = []
    for raw in names:
        name = member_name(raw)
        folded = name.casefold()
        if folded in seen:
            raise DataError("duplicate or case-colliding archive member")
        seen.add(folded)
        result.append(name)
    for name in seen:
        parts = name.split("/")
        if any("/".join(parts[:i]) in seen for i in range(1, len(parts))):
            raise DataError("file and directory member paths collide")
    return result


UpstreamArchive = runpy.run_path(str(Path(__file__).with_name("rpatool")))["RenPyArchive"]


class Archive(UpstreamArchive):
    def __init__(self, filename=None, *, version=3, key=0xDEADBEEF,
                 max_file=1024 * MIB, max_total=4096 * MIB):
        self.files, self.indexes = {}, {}
        self.handle = None
        self.max_file, self.max_total = max_file, max_total
        super().__init__(filename, version=version, key=key)

    def close(self):
        if self.handle is not None:
            self.handle.close()
            self.handle = None

    def get_version(self):
        self.handle.seek(0)
        self.header = self.handle.readline(128)
        if self.header.startswith(b"RPA-2.0 "):
            return 2
        if self.header.startswith(b"RPA-3.0 "):
            return 3
        raise DataError("only standard RPA-2.0 and RPA-3.0 are supported")

    def extract_indexes(self):
        fields = self.header.split()
        if len(fields) != (2 if self.version == 2 else 3):
            raise DataError("invalid RPA header")
        index_offset = int(fields[1], 16)
        if self.version == 3:
            self.key = int(fields[2], 16)
            if not 0 <= self.key <= 0xFFFFFFFF:
                raise DataError("RPA key exceeds 32 bits")
        self.handle.seek(0, os.SEEK_END)
        size = self.handle.tell()
        if not len(self.header) <= index_offset < size:
            raise DataError("index offset is outside archive data")
        if size - index_offset > INDEX_LIMIT:
            raise DataError("compressed index exceeds 64 MiB limit")
        self.handle.seek(index_offset)
        inflater = zlib.decompressobj()
        data = inflater.decompress(self.handle.read(), INDEX_LIMIT + 1)
        if len(data) > INDEX_LIMIT or not inflater.eof or inflater.unused_data:
            raise DataError("invalid or oversized compressed index")
        raw = read_pickle(data)
        if type(raw) is not dict or not raw or len(raw) > ENTRY_LIMIT:
            raise DataError("invalid or excessive archive entry count")
        names = validate_names(raw)
        result, total, chunk_count = {}, 0, 0
        for name, chunks in zip(names, raw.values()):
            if type(chunks) not in (list, tuple) or not chunks:
                raise DataError("invalid archive chunk list")
            validated, file_size = [], 0
            chunk_count += len(chunks)
            if chunk_count > CHUNK_LIMIT:
                raise DataError("too many archive chunks")
            for chunk in chunks:
                if type(chunk) not in (list, tuple) or len(chunk) not in (2, 3):
                    raise DataError("invalid archive chunk")
                offset, length = chunk[:2]
                if type(offset) is not int or type(length) is not int:
                    raise DataError("non-integer archive chunk offset or length")
                if self.version == 3:
                    offset, length = offset ^ self.key, length ^ self.key
                prefix = chunk[2] if len(chunk) == 3 else b""
                if type(prefix) is str:
                    prefix = prefix.encode("latin1", "strict")
                if type(prefix) is not bytes:
                    raise DataError("invalid archive chunk prefix")
                if offset < len(self.header) or length < 0 or offset + length > index_offset:
                    raise DataError("archive chunk is outside data section")
                file_size += len(prefix) + length
                if file_size > self.max_file:
                    raise DataError("archive member exceeds --max-file-mib")
                validated.append((offset, length, prefix))
            total += file_size
            if total > self.max_total:
                raise DataError("archive contents exceed --max-total-mib")
            result[name] = validated
        return result

    def read(self, filename):
        if filename in self.files:
            return self.files[filename]
        data = bytearray()
        for offset, length, prefix in self.indexes[filename]:
            self.handle.seek(offset)
            chunk = self.handle.read(length)
            if len(chunk) != length:
                raise DataError("truncated archive member")
            data.extend(prefix)
            data.extend(chunk)
        return bytes(data)


def positive_mib(value):
    result = int(value)
    if not 1 <= result <= 1_048_576:
        raise argparse.ArgumentTypeError("limit must be 1..1048576 MiB")
    return result * MIB


def no_symlink_path(path):
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise DataError("symbolic links and directory junctions are not supported")


def canonical_path_without_links(path):
    path = path.absolute()
    # Inspect the original spelling first: resolve() would hide link/.. paths.
    no_symlink_path(path)
    path = path.resolve(strict=False)
    no_symlink_path(path)
    return path


def extract(archive, output, overwrite):
    output = output.absolute()
    no_symlink_path(output)
    targets = []
    for name in archive.indexes:
        target = output.joinpath(*name.split("/"))
        no_symlink_path(target)
        if target.exists() and (not overwrite or not target.is_file()):
            raise DataError(f"output already exists: {target}")
        if any(p.exists() and not p.is_dir() for p in target.parents):
            raise DataError("output parent is not a directory")
        if target.resolve() == Path(archive.file).resolve():
            raise DataError("extraction would overwrite input archive")
        targets.append((name, target))
    for name, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb" if overwrite else "xb") as stream:
            for offset, length, prefix in archive.indexes[name]:
                stream.write(prefix)
                archive.handle.seek(offset)
                remaining = length
                while remaining:
                    chunk = archive.handle.read(min(remaining, MIB))
                    if not chunk:
                        raise DataError("truncated archive member")
                    stream.write(chunk)
                    remaining -= len(chunk)
    print(f"extracted {len(targets)} files")


def create(args):
    root = canonical_path_without_links(args.input)
    output = canonical_path_without_links(args.output)
    if not root.is_dir():
        raise DataError("input must be a directory")
    if output.is_relative_to(root):
        raise DataError("output archive must be outside input directory")
    if output.exists() and not args.overwrite:
        raise DataError("output archive already exists")
    files = []
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs.sort()
        for name in sorted(dirs + names):
            no_symlink_path(Path(current) / name)
        for name in sorted(names):
            path = Path(current) / name
            if not path.is_file():
                raise DataError("input contains a non-regular file")
            files.append((path.relative_to(root).as_posix(), path))
    if not files or len(files) > ENTRY_LIMIT:
        raise DataError("empty or excessive input file count")
    validate_names(name for name, _ in files)
    if not 0 <= args.key <= 0xFFFFFFFF:
        raise DataError("key must be an unsigned 32-bit integer")
    total = 0
    for _, path in files:
        size = path.stat().st_size
        total += size
        if size > args.max_file_mib or total > args.max_total_mib:
            raise DataError("input exceeds content size limits")
    archive = Archive(version=args.format, key=args.key,
                      max_file=args.max_file_mib, max_total=args.max_total_mib)
    temporary = None
    try:
        for name, path in files:
            archive.add(name, path.read_bytes())
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".rpatool-", suffix=".rpa", dir=output.parent, delete=False) as tmp:
            temporary = Path(tmp.name)
        archive.save(str(temporary))
        archive.close()
        os.replace(temporary, output)
        temporary = None
        print(str(output))
    finally:
        archive.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="rpatool 0.8 / GalSkill CLI 1")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("list", "extract", "create"):
        item = sub.add_parser(command)
        item.add_argument("--max-file-mib", type=positive_mib, default=1024 * MIB)
        item.add_argument("--max-total-mib", type=positive_mib, default=4096 * MIB)
        if command == "create":
            item.add_argument("input", type=Path)
            item.add_argument("--output", "-o", type=Path, required=True)
            item.add_argument("--format", type=int, choices=(2, 3), default=3)
            item.add_argument("--key", type=lambda value: int(value, 0), default=0xDEADBEEF)
        else:
            item.add_argument("archive", type=Path)
        if command == "extract":
            item.add_argument("--output", "-o", type=Path, required=True)
        if command in ("extract", "create"):
            item.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    archive = None
    try:
        if args.command == "create":
            create(args)
        else:
            archive = Archive(str(args.archive), max_file=args.max_file_mib, max_total=args.max_total_mib)
            if args.command == "list":
                for name in sorted(archive.indexes):
                    print(name)
            else:
                extract(archive, args.output, args.overwrite)
        return 0
    except (OSError, ValueError, TypeError, OverflowError, pickle.PickleError, zlib.error,
            EOFError, RecursionError) as error:
        print(f"rpatool: {error}", file=sys.stderr)
        return 1
    finally:
        if archive is not None:
            archive.close()


if __name__ == "__main__":
    raise SystemExit(main())
