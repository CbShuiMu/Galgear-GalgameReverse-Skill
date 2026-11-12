"""Trace the supported MUSICA SC instruction subset under explicit initial flags."""

import argparse
import json
import operator
import re
from pathlib import Path

from parse_musica_sc import coordinate, read_scripts


CONDITION = re.compile(r"([A-Za-z_]\w*)\s*(==|!=|<=|>=|<|>)\s*(-?\d+)\s+([^\s]+)")
ASSIGNMENT = re.compile(r"([A-Za-z_]\w*)\s*=\s*(-?\d+)")
COMPARISONS = {"==": operator.eq, "!=": operator.ne, "<=": operator.le, ">=": operator.ge,
               "<": operator.lt, ">": operator.gt}
LINEAR_COMMANDS = {
    "effect", "endScroll", "hscroll", "label", "movie", "panel", "playBGM", "playSE", "playSE2",
    "playVoice", "pragma", "scroll", "shakeScreen", "stage", "transition", "vscroll", "wait",
}


def trace(scripts, origins, entry, initial, *, step_limit=100_000):
    current = entry.casefold()
    if current not in scripts:
        raise ValueError(f"entry SC not found: {entry}")
    index = 0
    callers = []
    globals_ = dict(initial)
    locals_ = {}
    sources = {}
    messages = []
    control = []
    by_offset = {key: {op["byte_offset"]: i for i, op in enumerate(script["operations"])}
                 for key, script in scripts.items()}
    dialogue = {key: {row["byte_offset"]: row for row in script["dialogue"]}
                for key, script in scripts.items()}
    seen = set()
    termination = "end_of_file"
    for _ in range(step_limit):
        script = scripts[current]
        if current not in sources:
            sources[current] = {"group": origins[current], "file": script["file"], "sha256": script["sha256"]}
        operations = script["operations"]
        if index == len(operations):
            if not callers:
                break
            current, index = callers.pop()
            continue
        op = operations[index]
        position = coordinate(script, op, origins[current])
        command = op["command"]
        arg = op.get("arguments", "")
        state = (current, index, tuple(callers), frozenset(globals_.items()), frozenset(locals_.items()))
        if state in seen:
            raise ValueError(f'{script["file"]}:{op["line"]}: repeated execution state')
        seen.add(state)
        index += 1
        if command == "message":
            messages.append({**dialogue[current][op["byte_offset"]], "group": origins[current], "file": script["file"]})
            continue
        if command in LINEAR_COMMANDS:
            continue
        event = {"source": position, "command": command, "arguments": arg, "messages_before": len(messages)}
        control.append(event)
        try:
            if command == "end":
                termination = "end"
                break
            if command in {"set", "setGlobal"}:
                assignment = ASSIGNMENT.fullmatch(arg)
                if not assignment:
                    raise ValueError("unsupported assignment")
                name, value = assignment.groups()
                target, other = (globals_, locals_) if command == "setGlobal" else (locals_, globals_)
                if name in other:
                    raise ValueError(f"ambiguous local/global scope for {name}")
                target[name] = int(value)
                event["value"] = target[name]
                continue
            if command == "if":
                condition = CONDITION.fullmatch(arg)
                if not condition:
                    raise ValueError("unsupported condition")
                name, comparison, right, label = condition.groups()
                if name not in locals_ and name not in globals_:
                    raise ValueError(f"missing initial value for {name}")
                left = locals_[name] if name in locals_ else globals_[name]
                event["taken"] = COMPARISONS[comparison](left, int(right))
                if not event["taken"]:
                    continue
            if command in {"if", "goto"}:
                if command == "goto":
                    label = arg
                if label not in script["labels"]:
                    raise ValueError(f"missing local label {label}")
                target = script["labels"][label]
                index = by_offset[current][target["byte_offset"]]
                event["target"] = coordinate(script, target, origins[current])
            elif command in {"chain", "include"}:
                target_key = arg.casefold()
                if target_key not in scripts:
                    raise ValueError(f"missing target SC {arg}")
                target = scripts[target_key]
                event["target"] = coordinate(target, target["operations"][0], origins[target_key])
                if command == "include":
                    if target_key == current or any(caller == target_key for caller, _ in callers):
                        raise ValueError(f"recursive include {arg}")
                    callers.append((current, index))
                else:
                    callers.clear()
                    locals_.clear()
                current, index = target_key, 0
            else:
                raise ValueError(f"unsupported control opcode {command}")
        except ValueError as exc:
            raise ValueError(f'{script["file"]}:{op["line"]}: {exc}') from exc
    else:
        raise ValueError("SC step limit exceeded")
    return {
        "entry": entry, "initial_globals": initial, "final_globals": globals_,
        "termination": termination, "sources": list(sources.values()), "control": control, "messages": messages,
        "runtime_verified": False, "save_slot_mapping_verified": False,
    }


def load_layers(base, overlay=None, text_encoding="cp932", speaker_encoding="cp932"):
    scripts = read_scripts(base, "cp932", "cp932")
    origins = {key: "base" for key in scripts}
    if overlay:
        overrides = read_scripts(overlay, text_encoding, speaker_encoding)
        scripts.update(overrides)
        origins.update(dict.fromkeys(overrides, "overlay"))
    return scripts, origins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("entry")
    parser.add_argument("output", type=Path)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--text-encoding", default="cp932")
    parser.add_argument("--speaker-encoding", default="cp932")
    parser.add_argument("--initial", action="append", default=[], metavar="NAME=INT")
    args = parser.parse_args()
    try:
        initial = {}
        for item in args.initial:
            match = ASSIGNMENT.fullmatch(item)
            if not match or match[1] in initial:
                raise ValueError(f"invalid or repeated initial flag: {item}")
            initial[match[1]] = int(match[2])
        scripts, origins = load_layers(args.base, args.overlay, args.text_encoding, args.speaker_encoding)
        result = trace(scripts, origins, args.entry, initial)
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
            out.write("\n")
    except (OSError, ValueError, LookupError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps({"sources": len(result["sources"]), "messages": len(result["messages"]),
                      "termination": result["termination"]}))


if __name__ == "__main__":
    main()
