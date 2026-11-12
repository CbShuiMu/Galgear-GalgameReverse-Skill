"""Index Majiro V1 instructions, literal script transfers, and menu dispatch sites."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from parse_majiro_v1 import assemble_messages, read_majiro


# Symbol identities from majiro-py, revision f7ec450d5b78f0ed6df603b8c0b0ed79748d9cee.
SCRIPT_CALLS = {0x718EF651: "exec", 0xCD00D280: "call-script", 0x10DB0A43: "load-library"}
SAVE_CALLS = {0x89018DD1: "save", 0x3A3CA0F1: "load"}
MENUS = {0x0A7A489C, 0x57F252DB, 0x4B22CC66}
ALTERNATE_PC = {"bsel.1", "bsel.2", "bsel.3", "bsel.4", "bsel.5", "bsel.x"}
UNCONDITIONAL = {"br", "br.case"}


def script_key(name, original_name_encoding=None):
    if original_name_encoding:
        name = name.encode(original_name_encoding).decode("cp932")
    return (name if name.lower().endswith(".mjo") else name + ".mjo").casefold()


def read_layers(layers):
    scripts = {}
    history = defaultdict(list)
    for group, directory, text_encoding, name_encoding in layers:
        files = sorted((p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".mjo"),
                       key=lambda p: p.name.casefold())
        if not files:
            raise ValueError(f"{directory}: no MJO files")
        seen = set()
        for path in files:
            key = script_key(path.name, name_encoding)
            if key in seen:
                raise ValueError(f"{group}: ambiguous MJO name {path.name}")
            seen.add(key)
            history[key].append({"group": group, "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            scripts[key] = (group, path, text_encoding, name_encoding)
    return scripts, history


def code_location(offset, script, by_offset, source_lines, code_base):
    if offset not in by_offset:
        raise ValueError(f"{script}: non-instruction location {offset}")
    return {"code_offset": offset, "file_offset": code_base + offset, "source_line": source_lines[offset]}


def menu_dispatch(trace, at, by_offset, leaders):
    def skip_lines(index):
        while index < len(trace) and trace[index]["name"] == "line" and trace[index]["offset"] not in leaders:
            index += 1
        return index

    after = skip_lines(at + 1)
    stored = trace[after:after + 2]
    if len(stored) == 2 and [op["name"] for op in stored] == ["st.i", "pop"] and not any(
        op["offset"] in leaders for op in stored
    ):
        load = skip_lines(after + 2)
        if (load < len(trace) and trace[load]["name"] == "ld" and trace[load]["offset"] not in leaders
                and trace[load]["operands"] == stored[0]["operands"]):
            after = skip_lines(load + 1)
    if after == len(trace) or trace[after]["offset"] in leaders:
        return None
    dispatch = trace[after]
    if dispatch["name"] == "switch":
        return {"instruction": dispatch["offset"], "kind": "switch-table",
                "cases": [{"value": value, "target": target} for value, target in enumerate(dispatch["targets"])]}
    if dispatch["name"] != "br.case":
        return None

    next_case = dispatch["targets"][0]
    cases = []
    seen = set()
    while next_case not in seen:
        seen.add(next_case)
        index = by_offset[next_case]
        while index < len(trace) and trace[index]["name"] == "line":
            index += 1
        if index + 2 >= len(trace) or trace[index]["name"] != "ldc.i" or trace[index + 1]["name"] != "bne.case":
            break
        value = trace[index]["operands"][0]
        if any(case["value"] == value for case in cases):
            break
        cases.append({"value": value, "target": trace[index + 2]["offset"]})
        next_case = trace[index + 1]["targets"][0]
    if cases:
        return {"instruction": dispatch["offset"], "kind": "bne.case-chain",
                "cases": cases, "otherwise": next_case}
    return None


def inspect_script(key, group, path, text_encoding, name_encoding, templates, strip_script_suffix):
    _, _, trace, checks = read_majiro(path, templates, text_encoding)
    by_offset = {op["offset"]: index for index, op in enumerate(trace)}
    entries = set(checks["functions"])
    leaders = entries | {target for op in trace for target in op["targets"]}
    line = None
    source_lines = {}
    for op in trace:
        if op["offset"] in entries:
            line = None
        if op["name"] == "line":
            line = op["operands"][0]
        source_lines[op["offset"]] = line
    code_base = checks["code_base"]
    def locate(offset):
        return code_location(offset, key, by_offset, source_lines, code_base)

    branches = []
    transfers = []
    functions = []
    menus = []
    save_calls = []
    messages, options, _ = assemble_messages(trace)
    options_by_site = defaultdict(list)
    for option in options:
        if option["kind"] == "consumer-choice":
            options_by_site[option["consumer_offset"]].append(option)
    for at, op in enumerate(trace):
        offset, name, operands = op["offset"], op["name"], op["operands"]
        following = trace[at + 1]["offset"] if at + 1 < len(trace) else None
        if op["targets"] or name == "bsel.jmp.4":
            if name in ALTERNATE_PC:
                kind = "alternate-pc-registration"
            elif name == "bsel.jmp.4":
                kind = "alternate-pc-jump"
            elif name in UNCONDITIONAL:
                kind = "jump"
            elif name == "switch":
                kind = "switch"
            else:
                kind = "conditional"
            branches.append({"source": locate(offset), "command": name, "kind": kind,
                             "targets": [locate(target) for target in op["targets"]],
                             "next": locate(following) if following is not None and kind not in {"jump", "alternate-pc-jump"} else None})
        if name not in {"call", "callp", "syscall", "syscallp"}:
            continue
        consumer = operands[0] & 0xFFFFFFFF
        if name in {"call", "callp"}:
            functions.append({"source": locate(offset), "hash": consumer})
        elif consumer in SCRIPT_CALLS:
            reference = {"source": locate(offset), "command": SCRIPT_CALLS[consumer], "target_key": None}
            if len(operands) == 2 and operands[1] == 1 and offset not in leaders and at and trace[at - 1]["name"] == "ldstr":
                argument = trace[at - 1]
                reference["literal"] = argument["operands"][0]
                reference["argument"] = locate(argument["offset"])
                try:
                    literal = reference["literal"]
                    if strip_script_suffix and consumer == 0x718EF651 and literal.lower().endswith(".txt"):
                        literal = literal[:-4]
                        reference["name_transform"] = "strip-txt-suffix"
                    reference["target_key"] = script_key(literal, text_encoding if name_encoding else None)
                except UnicodeError:
                    reference["error"] = "script name cannot be interpreted using the selected encoding"
            transfers.append(reference)
        elif consumer in SAVE_CALLS:
            save_calls.append({"source": locate(offset), "command": SAVE_CALLS[consumer]})
        if consumer in MENUS:
            entry = {"source": locate(offset), "hash": consumer, "options": options_by_site[offset],
                     "dispatch": menu_dispatch(trace, at, by_offset, leaders) if name in {"call", "syscall"} else None}
            menus.append(entry)
    return {
        "script": key, "file": path.name, "group": group, "main": locate(checks["main_offset"]),
        "functions": [{"hash": fn["hash"], "target": locate(fn["offset"])} for fn in checks["function_table"]],
        "code_base": code_base, "declared_line_count": checks["declared_line_count"],
        "instruction_count": len(trace), "branches": branches, "script_transfers": transfers,
        "function_calls": functions, "menus": menus, "save_commands": save_calls, "messages": messages,
    }


def index(layers, *, strip_script_suffix=False):
    templates = Path(__file__).resolve().parents[1] / "assets/majiro-v1-opcodes.json"
    inputs, history = read_layers(layers)
    scripts = {}
    for key, source in sorted(inputs.items()):
        scripts[key] = inspect_script(key, *source, templates, strip_script_suffix)
        scripts[key]["source_history"] = history[key]

    functions = defaultdict(list)
    for key, script in scripts.items():
        for entry in script["functions"]:
            functions[entry["hash"]].append({"script": key, "target": entry["target"]})
    for key, script in scripts.items():
        for ref in script["script_transfers"]:
            target = scripts.get(ref["target_key"])
            ref["status"] = "resolved" if target else ("missing-script" if ref["target_key"] else "dynamic")
            if target:
                ref["target"] = target["main"]
        for ref in script["function_calls"]:
            candidates = functions.get(ref["hash"], [])
            local = [candidate for candidate in candidates if candidate["script"] == key]
            ref["candidates"] = local or candidates
            ref["status"] = "local" if len(local) == 1 else ("external-candidate" if candidates else "unresolved")
    return {"format": "majiro-v1-flow", "scripts": list(scripts.values()),
            "runtime_verified": False, "save_slot_mapping_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--update", type=Path)
    parser.add_argument("--localized", type=Path)
    parser.add_argument("--localized-text-encoding", default="gb18030")
    parser.add_argument("--localized-name-encoding", help="codec originally used to display raw CP932 filenames")
    parser.add_argument("--strip-script-suffix", action="store_true",
                        help="accept .txt in literal exec arguments after confirming native basename lookup")
    args = parser.parse_args()
    layers = [("base", args.base, "cp932", None)]
    if args.update:
        layers.append(("update", args.update, "cp932", None))
    if args.localized:
        layers.append(("localized", args.localized, args.localized_text_encoding, args.localized_name_encoding))
    try:
        result = index(layers, strip_script_suffix=args.strip_script_suffix)
        with args.output.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except (OSError, ValueError, LookupError) as exc:
        parser.exit(1, f"{exc}\n")
    scripts = result["scripts"]
    print(json.dumps({"scripts": len(scripts),
                      "script_transfers": sum(len(s["script_transfers"]) for s in scripts),
                      "menus": sum(len(s["menus"]) for s in scripts)}))


if __name__ == "__main__":
    main()
