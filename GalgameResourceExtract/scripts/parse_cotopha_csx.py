"""Validate indexed Cotopha CSX strings and bind literal dialogue to disassembly."""

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import struct


ENTIS = b"Entis\x1a\0\0"
INSTRUCTION = re.compile(r"([0-9A-Fa-f]{8}) \| (.*)")
INDEXED_LOAD = re.compile(r'Load String ".*" \((\d+)\)')
FUNCTION = re.compile(r'Enter "([^"]+)" \(')
BRANCH = re.compile(r"(Jump|CJump \d+) ([0-9A-Fa-f]{8})")
MESSAGE = 'ExCall "WitchWizard::OutMsg" <8>'


def sections(data, magic):
    if len(data) < 64 or data[:8] != ENTIS or not data[16:64].startswith(magic):
        raise ValueError("unexpected Entis file type")
    result = {}
    at = 64
    while at < len(data):
        if len(data) - at < 16:
            raise ValueError("truncated section header")
        tag, length = struct.unpack_from("<8sq", data, at)
        body = at + 16
        if length < 0 or length > len(data) - body or tag in result:
            raise ValueError(f"invalid or repeated section {tag!r} at {at:#x}")
        at = body + length
        result[tag] = (body, memoryview(data)[body:at])
    return result


def read_string(data, pos):
    if pos + 4 > len(data):
        raise ValueError("truncated string length")
    units, = struct.unpack_from("<I", data, pos)
    end = pos + 4 + units * 2
    if end > len(data):
        raise ValueError("truncated UTF-16LE string")
    return bytes(data[pos + 4:end]).decode("utf-16le"), end


def read_constants(data, image):
    if len(data) < 4:
        raise ValueError("missing constant count")
    count, = struct.unpack_from("<I", data)
    if count > (len(data) - 4) // 8:
        raise ValueError("constant count exceeds section")
    values = []
    pos = 4
    refs = 0
    for index in range(count):
        value, pos = read_string(data, pos)
        if pos + 4 > len(data):
            raise ValueError("missing reference count")
        n, = struct.unpack_from("<I", data, pos)
        pos += 4
        end = pos + 4*n
        if end > len(data):
            raise ValueError("truncated reference list")
        for (at,) in struct.iter_unpack("<I", data[pos:end]):
            if at < 4 or at + 4 > len(image) or struct.unpack_from("<II", image, at - 4) != (0x80000000, index):
                raise ValueError(f"constant {index} has an unsupported image reference at {at:#x}")
        values.append(value)
        refs += n
        pos = end
    if pos != len(data):
        raise ValueError("constant table has remaining bytes")
    return values, refs


def text_load(row, image, constants):
    at, asm = row
    match = INDEXED_LOAD.fullmatch(asm)
    if not match or at + 11 > len(image) or image[at:at + 3] != b"\x02\0\x06":
        raise ValueError("expected indexed string load")
    index = int(match[1])
    if index >= len(constants) or struct.unpack_from("<II", image, at + 3) != (0x80000000, index):
        raise ValueError("indexed string does not match CSX bytecode")
    return {"index": index, "image_offset": at, "value": constants[index]}


def message_arguments(recent, image, constants):
    if len(recent) < 8:
        raise ValueError("missing message arguments")
    numbers = []
    for at, asm in recent[-4:]:
        if not asm.startswith("Load Integer ") or at + 7 > len(image) or image[at:at + 3] != b"\x02\0\x04":
            raise ValueError("unsupported message numeric argument")
        value = int(asm.removeprefix("Load Integer "))
        if not -(1 << 31) <= value < (1 << 32) or struct.unpack_from("<I", image, at + 3)[0] != (value & 0xFFFFFFFF):
            raise ValueError("message integer does not match CSX bytecode")
        numbers.append(value)
    voice_list = []
    cursor = len(recent) - 5
    while cursor >= 4 and recent[cursor][1] == "Operate.Add":
        voice_list.append(text_load(recent[cursor - 1], image, constants))
        cursor -= 2
    if cursor < 3 or recent[cursor][1] != 'Load New "ECSArray"' or recent[cursor - 3][1] != "Load Global [0]":
        raise ValueError("unsupported message receiver or voice array")
    return text_load(recent[cursor - 2], image, constants), text_load(recent[cursor - 1], image, constants), list(reversed(voice_list)), numbers


def parse_script(path, assembly):
    data = path.read_bytes()
    parts = sections(data, b"Cotopha Image file")
    if b"image   " not in parts or b"conststr" not in parts:
        raise ValueError("CSX image and indexed strings required")
    base, image = parts[b"image   "]
    values, refs = read_constants(parts[b"conststr"][1], image)
    recent = deque(maxlen=40)
    boundaries = set()
    messages, branches, errors = [], [], []
    functions = {}
    call_targets = []
    owner = None
    previous = -1
    total_messages = 0
    for line in assembly:
        match = INSTRUCTION.fullmatch(line.rstrip("\r\n"))
        if not match:
            raise ValueError("unexpected disassembly line")
        address = int(match[1], 16)
        asm = match[2]
        if not previous < address < len(image):
            raise ValueError(f"disassembly offset out of order at {address:#x}")
        previous = address
        boundaries.add(address)
        function = FUNCTION.match(asm)
        if function:
            owner = function[1]
            functions[address] = owner
        branch = BRANCH.fullmatch(asm)
        if branch:
            offset = 1 if branch[1] == "Jump" else 2
            target = int(branch[2], 16)
            if (image[address] != (6 if offset == 1 else 7)
                    or target != address + offset + 4 + struct.unpack_from("<i", image, address + offset)[0]):
                raise ValueError(f"branch target does not match bytecode at {address:#x}")
            branches.append({"image_offset": address, "target": target, "function": owner, "kind": branch[1]})
        if asm == MESSAGE:
            total_messages += 1
            try:
                if image[address:address+7] != b"\x11\x08\0\0\0\0\x04":
                    raise ValueError("unsupported message call form")
                target, = struct.unpack_from("<I", image, address+7)
                call_targets.append(target)
                name, body, voices, args = message_arguments(list(recent), image, values)
                messages.append({"image_offset": address, "file_offset": base+address, "function": owner,
                                 "speaker": name, "text": body, "voices": voices, "arguments": args})
            except (ValueError, struct.error) as exc:
                errors.append({"image_offset": address, "error": str(exc)})
        recent.append((address, asm))
    if not boundaries:
        raise ValueError("no disassembly instructions")
    for edge in branches:
        target = edge["target"]
        edge["target_status"] = ("instruction" if target in boundaries else
                                 "end-of-image" if target == len(image) else "unresolved")
    if any(functions.get(at) != "WitchWizard::OutMsg" for at in call_targets):
        raise ValueError("message call does not resolve to WitchWizard::OutMsg")
    return {"sha256": hashlib.sha256(data).hexdigest(), "image_offset": base,
            "sections": {k.decode("ascii").rstrip(): [at, len(v)] for k, (at, v) in parts.items()},
            "string_count": len(values), "empty_strings": values.count(""), "references": refs,
            "instruction_count": len(boundaries), "functions": functions, "message_calls": total_messages,
            "messages": messages, "branches": branches, "message_errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("disassembly", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        with args.disassembly.open(encoding="utf-8-sig") as assembly:
            report = parse_script(args.script, assembly)
        with args.output.open("x", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except (OSError, ValueError, struct.error) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps({"strings": report["string_count"], "references": report["references"],
                      "messages": len(report["messages"]), "unresolved": len(report["message_errors"]),
                      "branches": len(report["branches"]),
                      "unresolved_branches": sum(b["target_status"] == "unresolved" for b in report["branches"])}))


if __name__ == "__main__":
    main()
