"""Locate validated MJO frame runs in MajiroSavV1.105 slot files."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct

from parse_majiro_v1 import assemble_messages, read_majiro


SIGNATURE = b"MajiroSavV1.105\0"
FRAME_SIZE = 168
NAME_SIZE = 128


def name_key(name):
    return name.lower() if name.isascii() else name


def match_frames(data, names, resolver):
    if not data.startswith(SIGNATURE):
        raise ValueError("expected a MajiroSavV1.105 slot")
    if not names:
        raise ValueError("no matching MJO filenames")
    ordered = sorted(names, key=lambda name: (-len(name), name))
    patterns = [rb"(?i:" + re.escape(name) + b")" if name.isascii() else re.escape(name) for name in ordered]
    matcher = re.compile(rb"(?:" + b"|".join(patterns) + rb")\x00")
    frames = {}
    for match in matcher.finditer(data, len(SIGNATURE)):
        offset = match.start()
        if offset + FRAME_SIZE > len(data) or match.end() > offset + NAME_SIZE:
            continue
        if any(data[match.end():offset + NAME_SIZE]):
            continue
        pc, _, _, _, line = struct.unpack_from("<5I", data, offset + NAME_SIZE)
        candidates = resolver(name_key(match.group()[:-1]), pc, line)
        if candidates:
            frames[offset] = {"slot_offset": offset, "script_pc": pc, "line_value": line, "matches": candidates}
    runs = []
    for offset in sorted(frames):
        if offset - FRAME_SIZE in frames or offset + FRAME_SIZE not in frames:
            continue
        run = []
        while offset in frames:
            run.append(frames[offset])
            offset += FRAME_SIZE
        runs.append(run)
    if not runs:
        raise ValueError("no consecutive frames matched script instruction boundaries")
    return runs


def locate(slot, script_root, encoding):
    templates = Path(__file__).resolve().parents[1] / "assets/majiro-v1-opcodes.json"
    names = defaultdict(list)
    diagnostics = {}
    for path in sorted(script_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".mjo":
            continue
        try:
            name = name_key(path.name.encode(encoding))
        except UnicodeError:
            diagnostics[path.relative_to(script_root).as_posix()] = "filename does not round-trip with selected encoding"
            continue
        if len(name) < NAME_SIZE:
            names[name].append(path)
    cache = {}

    def resolve(name, pc, line):
        candidates = []
        for path in names[name]:
            if path not in cache:
                try:
                    _, _, trace, checks = read_majiro(path, templates, encoding)
                except (OSError, ValueError) as exc:
                    diagnostics[path.relative_to(script_root).as_posix()] = str(exc)
                    cache[path] = None
                else:
                    messages, _, _ = assemble_messages(trace)
                    cache[path] = ({op["offset"]: op for op in trace},
                                   [(op["offset"], op["operands"][0]) for op in trace if op["name"] == "line"],
                                   messages, checks["code_base"], hashlib.sha256(path.read_bytes()).hexdigest())
            if cache[path] is None:
                continue
            opcodes, lines, messages, base, digest = cache[path]
            if pc not in opcodes:
                continue
            prior_line = next((value for offset, value in reversed(lines) if offset < pc), None)
            next_line = next((value for offset, value in lines if offset >= pc), None)
            if line and prior_line is not None and next_line is not None and not prior_line <= line <= next_line:
                continue
            preceding = next((m for m in reversed(messages) if max(m["instruction_offsets"]) <= pc), None)
            candidates.append({
                "script": path.relative_to(script_root).as_posix(), "sha256": digest,
                "file_offset": base + pc, "opcode": opcodes[pc]["name"],
                "preceding_line": prior_line, "next_line": next_line, "preceding_message": preceding,
            })
        return candidates

    data = slot.read_bytes()
    runs = match_frames(data, names, resolve)
    return {
        "slot": slot.name, "sha256": hashlib.sha256(data).hexdigest(), "frame_runs": runs,
        "script_diagnostics": diagnostics, "runtime_restore_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slot", type=Path)
    parser.add_argument("scripts", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--encoding", default="cp932")
    args = parser.parse_args()
    try:
        result = locate(args.slot, args.scripts, args.encoding)
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
            out.write("\n")
    except (OSError, ValueError, LookupError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps({"runs": len(result["frame_runs"]),
                      "frames": sum(len(run) for run in result["frame_runs"])}))


if __name__ == "__main__":
    main()
