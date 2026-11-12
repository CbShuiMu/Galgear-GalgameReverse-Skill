"""Extract MUSICA SC dialogue and literal control-flow references without running the engine."""

import argparse
import hashlib
import json
import re
from pathlib import Path


COMMAND = re.compile(rb"^[ \t]*\.(\w+)(?:[ \t](.*))?$")
SEPARATOR = re.compile(rb"[ \t]")
BRANCHES = {"if", "goto", "chain"}
ANNOTATIONS = {"set", "setGlobal", "pragma"}


def parse_script(path, text_encoding, speaker_encoding):
    source = path.read_bytes()
    operations = []
    dialogue = []
    labels = {}
    position = 0
    for number, raw in enumerate(source.splitlines(keepends=True), 1):
        offset = position
        position += len(raw)
        match = COMMAND.fullmatch(raw.rstrip(b"\r\n"))
        if not match:
            continue
        command = match[1].decode("ascii")
        arguments = match[2] or b""
        operation = {"line": number, "byte_offset": offset + match.start(1) - 1, "command": command}
        operations.append(operation)
        try:
            if command == "message":
                identifier, voice, speaker, body = SEPARATOR.split(arguments, maxsplit=3)
                if not identifier.isdigit():
                    raise ValueError("expected a numeric message ID")
                marked = speaker.startswith(b"@")
                if marked:
                    speaker = speaker[1:]
                dialogue.append({
                    **operation,
                    "message_id": int(identifier),
                    "voice_ref": voice.decode("ascii") or None,
                    "speaker": speaker.decode(speaker_encoding).strip() or None,
                    "speaker_marked": marked,
                    "text": body.decode(text_encoding),
                })
            elif command == "label":
                label = arguments.strip().decode("ascii")
                if not label or label in labels:
                    raise ValueError("expected a unique nonempty label")
                labels[label] = operation
                operation["label"] = label
            elif command in BRANCHES | ANNOTATIONS | {"select", "end"}:
                operation["arguments"] = arguments.decode(text_encoding).strip()
        except ValueError as exc:
            raise ValueError(f"{path.name}:{number}: {command}: {exc}") from exc
    if not operations:
        raise ValueError(f"{path.name}: no SC commands")
    return {
        "file": path.name,
        "size": len(source),
        "sha256": hashlib.sha256(source).hexdigest(),
        "operations": operations,
        "labels": labels,
        "dialogue": dialogue,
    }


def read_scripts(root, text_encoding, speaker_encoding):
    scripts = {}
    for path in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if not path.is_file() or path.suffix.lower() != ".sc":
            continue
        key = path.name.casefold()
        if key in scripts:
            raise ValueError(f"ambiguous SC filename: {path.name}")
        scripts[key] = parse_script(path, text_encoding, speaker_encoding)
    if not scripts:
        raise ValueError(f"{root}: no SC files")
    return scripts


def coordinate(script, operation, group="input"):
    if operation is None:
        return None
    return {"group": group, "file": script["file"], "line": operation["line"],
            "byte_offset": operation["byte_offset"]}


def build_flow(scripts, base_scripts):
    references = []
    for script in scripts.values():
        operations = script["operations"]
        for index, operation in enumerate(operations):
            command = operation["command"]
            if command not in BRANCHES | {"select", "end"}:
                continue
            reference = {
                "source": coordinate(script, operation),
                "command": command,
                "arguments": operation["arguments"],
            }
            literal = operation["arguments"]
            if command == "if":
                fields = literal.rsplit(maxsplit=1)
                if len(fields) != 2:
                    raise ValueError(f'{script["file"]}:{operation["line"]}: malformed .if')
                reference["condition"], literal = fields
                following = operations[index + 1] if index + 1 < len(operations) else None
                reference["fallthrough"] = coordinate(script, following)
            if command in {"if", "goto"}:
                reference["target"] = coordinate(script, script["labels"].get(literal))
            elif command == "chain":
                target = scripts.get(literal.casefold())
                group = "input"
                if target is None:
                    target = base_scripts.get(literal.casefold())
                    group = "chain-base"
                reference["target"] = coordinate(target, target["operations"][0], group) if target else None
            else:
                reference["target"] = None
            if command in BRANCHES:
                reference["literal_target"] = literal
                reference["status"] = "resolved" if reference["target"] else "unresolved"
            else:
                reference["status"] = "terminal" if command == "end" else "unparsed-choice"
            references.append(reference)
    return references


def extract(root, text_encoding, speaker_encoding, chain_base=None):
    scripts = read_scripts(root, text_encoding, speaker_encoding)
    base_scripts = read_scripts(chain_base, "cp932", "cp932") if chain_base else {}
    references = build_flow(scripts, base_scripts)
    for script in scripts.values():
        script.pop("labels")
    return {
        "format": "musica-sc",
        "text_encoding": text_encoding,
        "speaker_encoding": speaker_encoding,
        "scripts": list(scripts.values()),
        "chain_base": [
            {field: script[field] for field in ("file", "size", "sha256")}
            for script in base_scripts.values()
        ],
        "control_flow": references,
        "runtime_verified": False,
        "save_slot_mapping_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="flat directory of SC files from one script group")
    parser.add_argument("output", type=Path, help="new JSON file")
    parser.add_argument("--text-encoding", choices=("cp932", "gbk", "gb18030", "utf-8"), default="cp932")
    parser.add_argument("--speaker-encoding", choices=("cp932", "gbk", "gb18030", "utf-8"))
    parser.add_argument("--chain-base", type=Path, help="verified CP932 base group for missing .chain targets")
    args = parser.parse_args()
    speaker_encoding = args.speaker_encoding or args.text_encoding
    try:
        report = extract(args.input, args.text_encoding, speaker_encoding, args.chain_base)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    references = report["control_flow"]
    print(json.dumps({
        "scripts": len(report["scripts"]),
        "messages": sum(len(script["dialogue"]) for script in report["scripts"]),
        "resolved": sum(ref["status"] == "resolved" for ref in references),
        "unresolved": sum(ref["status"] == "unresolved" for ref in references),
    }))


if __name__ == "__main__":
    main()
