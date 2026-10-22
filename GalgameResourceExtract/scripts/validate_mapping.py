"""Check a dialogue mapping and optional byte evidence without a host API.

Only file identities, byte ranges and resource paths are checked automatically.
Parser semantics and the relation between dialogue and voice need separate proof.
"""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import json
import sys


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def relative_file(root, value):
    if not isinstance(value, str) or not value or PureWindowsPath(value).drive:
        raise ValueError(f'Expected a relative file path: {value!r}')
    parts = value.replace('\\', '/').split('/')
    if any(p in {'', '.', '..'} or ':' in p or p.endswith((' ', '.')) for p in parts):
        raise ValueError(f'Unsafe relative path: {value!r}')
    path = (root / '/'.join(parts)).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'File must be within the supplied root: {value}')
    return path


def file_hash(path, offset=0, length=None):
    remaining = path.stat().st_size - offset if length is None else length
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        stream.seek(offset)
        while remaining:
            chunk = stream.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError(f'Truncated file: {path}')
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def mapping_rows(value):
    if isinstance(value, dict):
        if value.get('kind', 'gal-dialogue-map') != 'gal-dialogue-map' or value.get('schema_version', 1) != 1:
            raise ValueError('Unsupported dialogue mapping kind or version')
        value = value.get('entries')
    if not isinstance(value, list) or not value:
        raise ValueError('Expected a nonempty mapping list')
    return value


def verify_evidence(value, source_root, rows):
    if value.get('kind') != 'gal-dialogue-evidence' or value.get('schema_version') != 1:
        raise ValueError('Expected gal-dialogue-evidence schema_version 1')
    files = value.get('files')
    entries = value.get('entries')
    if not isinstance(files, dict) or not files or not isinstance(entries, list):
        raise ValueError('Evidence needs files and entries')
    resolved = {}
    for key, info in files.items():
        path = relative_file(source_root, info['path'])
        if file_hash(path) != info['sha256']:
            raise ValueError(f'Evidence source changed: {key}')
        resolved[key] = path
    seen, count = set(), 0
    for entry in entries:
        row = entry.get('row')
        if type(row) is not int or not 0 <= row < len(rows) or row in seen:
            raise ValueError('Evidence row must be a unique mapping row index')
        seen.add(row)
        if entry.get('dialogue_id') != rows[row].get('dialogue_id'):
            raise ValueError(f'Evidence dialogue_id differs at row {row}')
        if not isinstance(entry.get('relation'), str) or not entry['relation'].strip():
            raise ValueError(f'Row {row}: document the message/voice relation')
        spans = entry.get('spans')
        if not isinstance(spans, list) or not spans:
            raise ValueError(f'Row {row}: missing byte spans')
        roles = set()
        for span in spans:
            path = resolved[span['file']]
            offset, length = span['offset'], span['length']
            if (type(offset) is not int or type(length) is not int or offset < 0 or length <= 0
                    or offset > path.stat().st_size or length > path.stat().st_size - offset):
                raise ValueError(f'Row {row}: evidence span is outside the file')
            if span.get('role') not in {'message', 'speaker', 'voice', 'reference'}:
                raise ValueError(f'Row {row}: unknown evidence role')
            roles.add(span['role'])
            if file_hash(path, offset, length) != span['sha256']:
                raise ValueError(f'Row {row}: evidence bytes changed')
            count += 1
        required = {'message', 'voice'} | ({'speaker'} if rows[row].get('speaker') is not None else set())
        if not required <= roles:
            raise ValueError(f'Row {row}: missing message, voice or displayed-speaker evidence')
    if seen != set(range(len(rows))):
        raise ValueError('Evidence must cover every mapping row')
    return dict(files=len(resolved), spans=count, integrity='passed', semantics='not_automatically_verified')


def validate(mapping, asset_root, evidence=None, source_root=None):
    root = Path(asset_root).resolve(strict=True)
    rows = mapping_rows(mapping)
    ids, resources, text_by_path, unresolved = set(), set(), {}, []
    references = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get('chinese_text'), str):
            raise ValueError(f'Row {index}: chinese_text must be a string')
        identifier = row.get('dialogue_id')
        if identifier is not None:
            if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
                raise ValueError('dialogue_id must be a unique nonempty string')
            ids.add(identifier)
        if row.get('speaker') is not None and not isinstance(row['speaker'], str):
            raise ValueError('speaker must be a string or null')
        if row.get('source') is not None and not isinstance(row['source'], dict):
            raise ValueError('source must be an object')
        names, paths = row.get('audio_files'), row.get('audio_paths')
        if not isinstance(names, list) or not names or not isinstance(paths, list) or len(names) != len(paths):
            raise ValueError(f'Row {index}: explicit audio_files/audio_paths must align')
        segments = row.get('audio_segments')
        if segments is not None and (not isinstance(segments, list) or len(segments) != len(names)
                or any(not isinstance(s, dict) or not isinstance(s.get('chinese_text'), str) for s in segments)):
            raise ValueError(f'Row {index}: audio_segments must contain one chinese_text per audio file')
        if len(names) > 1 and segments is None:
            unresolved.append(dict(row=index, reason='multiple audio files need explicit audio_segments before TTS'))
        for voice_index, (name, relative) in enumerate(zip(names, paths)):
            if not isinstance(name, str) or not name or PureWindowsPath(name).name != name or '/' in name:
                raise ValueError(f'Row {index}: audio_files must contain basenames')
            path = relative_file(root, relative)
            if path.name != name or str(relative).replace('\\', '/').split('/')[0].casefold() == '.galtts':
                raise ValueError(f'Row {index}: resource name differs or uses reserved .galtts path')
            key = path.relative_to(root).as_posix().casefold()
            resources.add(key)
            references += 1
            if len(names) == 1 or segments is not None:
                import re
                text = row['chinese_text'] if segments is None else segments[voice_index]['chinese_text']
                text = re.sub(r'\s+', ' ', re.sub(r'\\+[nr]', ' ', text)).strip()
                if key in text_by_path and text_by_path[key] != text:
                    unresolved.append(dict(row=index, reason=f'conflicting text for shared audio: {relative}'))
                text_by_path[key] = text
    evidence_result = dict(integrity='not_supplied', semantics='not_automatically_verified')
    if evidence is not None:
        if source_root is None:
            raise ValueError('--source-root is required with --evidence')
        evidence_result = verify_evidence(evidence, Path(source_root).resolve(strict=True), rows)
    return dict(valid=True, rows=len(rows), voice_references=references, unique_resources=len(resources),
                tts_ready=not unresolved, unresolved=unresolved, evidence=evidence_result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    result = validate(read_json(args.mapping), args.asset_root,
                      read_json(args.evidence) if args.evidence else None, args.source_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['tts_ready'] else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
