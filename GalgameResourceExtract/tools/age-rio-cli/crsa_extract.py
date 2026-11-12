"""Extract checksum-verified CRsa records from an rUGP directory inventory."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
from rUGP.formats.rio.crypto import RIO_KEY, decode_encrypted_block

MAX_RECORD = 16 * 1024 * 1024


def decode_record(record):
    if record.startswith(b"\x00\x05\x6e\x03\x01\x00"):
        header_size = 11
    elif record[3:7] == b"\x6e\x03\x01\x00":
        header_size = 12
    else:
        raise ValueError("unrecognized CRsa object header")
    block = decode_encrypted_block(record[header_size:], RIO_KEY)
    tail_size = len(block.plaintext) % 32
    end = header_size + block.consumed
    if not block.plaintext or len(record) != end + (2 if tail_size else 0):
        raise ValueError("CRsa extent does not match the encrypted block")
    if tail_size:
        tail = block.plaintext[-tail_size:]
        checksum = sum(value * (tail_size - index) for index, value in enumerate(tail)) & 0xffff
        if checksum != int.from_bytes(record[end:], "little"):
            raise ValueError("CRsa final partial checksum mismatch")
    return header_size, block.plaintext


def extract(inventory, output, volumes):
    doc = json.loads(inventory.read_text(encoding="utf-8"))
    if doc.get("schema") != "muvluv-rugp-rio-inventory/v1":
        raise ValueError("unsupported inventory schema")
    sources = {path.name: path for path in volumes}
    if len(sources) != len(volumes):
        raise ValueError("duplicate volume basename")
    entries = [row for row in doc["nodes"] if row.get("class") == "CRsa"]
    if not entries:
        raise ValueError("no CRsa nodes in the inventory")
    sizes = {name: path.stat().st_size for name, path in sources.items()}
    output.mkdir()
    failures = 0
    with (output / "manifest.jsonl").open("x", encoding="utf-8") as log:
        for index, row in enumerate(entries):
            name = row["volume"]
            at, extent = row["volume_offset"], row["extent"]
            item = {"entry": index, "volume": name, "offset": at, "extent": extent,
                    "logical_path": row.get("logical_path")}
            native = output / f"{index:06}.crsa"
            decoded = output / f"{index:06}.plain"
            try:
                if (name not in sources or type(at) is not int or type(extent) is not int
                        or at < 0 or not 0 < extent <= MAX_RECORD or at + extent > sizes[name]):
                    raise ValueError("unbound or out-of-range CRsa extent")
                with sources[name].open("rb") as stream:
                    stream.seek(at)
                    record = stream.read(extent)
                if len(record) != extent:
                    raise ValueError("short CRsa extent")
                header_size, plaintext = decode_record(record)
                native.write_bytes(record)
                decoded.write_bytes(plaintext)
                item.update(status="ok", header_size=header_size, native=native.name,
                            plain=decoded.name, native_sha256=hashlib.sha256(record).hexdigest(),
                            plain_sha256=hashlib.sha256(plaintext).hexdigest())
            except (ValueError, OSError) as exc:
                failures += 1
                native.unlink(missing_ok=True)
                decoded.unlink(missing_ok=True)
                item.update(status="error", error=str(exc))
            log.write(json.dumps(item, ensure_ascii=True) + "\n")
    return {"listed": len(entries), "decoded": len(entries) - failures, "failed": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--volume", action="append", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = extract(args.inventory, args.output, args.volume)
        print(json.dumps(result))
        return int(bool(result["failed"]))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
