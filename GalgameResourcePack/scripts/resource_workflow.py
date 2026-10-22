"""Snapshot, merge, pack and verify one archive using shared resource manifests.

Uses only the Python standard library. Does not parse dialogue or select TTS models.
"""
from pathlib import Path, PureWindowsPath
import argparse
from datetime import datetime, timezone
import hashlib
import json
import stat
import subprocess
import sys
import tempfile


KIND = 'gal-resource-manifest'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_new(path, value):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def relative_path(value):
    if not isinstance(value, str) or not value or PureWindowsPath(value).drive:
        raise ValueError(f'Unsafe resource path: {value!r}')
    value = value.replace('\\', '/')
    if any(part in {'', '.', '..'} or ':' in part or part.endswith((' ', '.')) for part in value.split('/')):
        raise ValueError(f'Unsafe resource path: {value!r}')
    return value


def file_info(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f'Expected a file: {path}')
    return dict(path=str(path), size=path.stat().st_size, sha256=sha(path))


def check_file(info):
    actual = file_info(info['path'])
    if actual['sha256'] != info['sha256'] or ('size' in info and actual['size'] != info['size']):
        raise ValueError(f'File changed or checksum differs: {actual["path"]}')
    return Path(actual['path'])


def scan(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f'Expected a directory: {root}')
    result = {}

    def walk(directory):
        for path in sorted(directory.iterdir()):
            attrs = path.lstat()
            if stat.S_ISLNK(attrs.st_mode) or getattr(attrs, 'st_file_attributes', 0) & 0x400:
                raise ValueError(f'Resource links are unsupported: {path}')
            if path.is_dir():
                walk(path)
            elif path.is_file():
                name = relative_path(path.relative_to(root).as_posix())
                key = name.casefold()
                if key in result:
                    raise ValueError(f'Case-insensitive resource collision: {name}')
                result[key] = dict(path=name, source=file_info(path))
            else:
                raise ValueError(f'Unsupported resource: {path}')
    walk(root)
    return result


def load_manifest(path, stage):
    value = read(path)
    if (value.get('kind') != KIND or value.get('schema_version') != 1
            or value.get('stage') != stage or value.get('complete') is not True):
        raise ValueError(f'Expected a complete {stage} resource manifest: {path}')
    entries = value.get('entries')
    if not isinstance(entries, list) or not entries:
        raise ValueError(f'Manifest contains no resources: {path}')
    seen = set()
    for entry in entries:
        name = relative_path(entry['path'])
        if name.casefold() in seen:
            raise ValueError(f'Duplicate resource path: {name}')
        seen.add(name.casefold())
    return value


def outside(path, roots):
    path = Path(path).resolve()
    for root in roots:
        if path.is_relative_to(Path(root).resolve()):
            raise ValueError(f'Output must be outside resource directories: {path}')
    return path


def fresh_directory(path, roots):
    path = outside(path, roots)
    if path.exists():
        raise FileExistsError(f'Use a new directory: {path}')
    for root in roots:
        if Path(root).resolve().is_relative_to(path):
            raise ValueError(f'Output directory contains an input directory: {path}')
    return path


def compare_tree(root, entries):
    actual = scan(root)
    expected = {relative_path(e['path']).casefold(): e for e in entries}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = [expected[key]['path'] for key in sorted(set(expected) & set(actual))
               if actual[key]['source']['sha256'] != expected[key]['expected_sha256']]
    return dict(passed=not (missing or extra or changed), missing=missing, unexpected=extra, changed=changed,
                normalized_paths=[dict(expected=expected[key]['path'], actual=actual[key]['path'])
                                  for key in sorted(set(expected) & set(actual))
                                  if expected[key]['path'] != actual[key]['path']])


def require_tree(root, entries):
    report = compare_tree(root, entries)
    if not report['passed']:
        raise ValueError('Resource tree differs from manifest: ' + json.dumps(report, ensure_ascii=False))


def init(args):
    root = args.original_root.resolve(strict=True)
    output = outside(args.manifest, [root])
    if output.exists():
        raise FileExistsError(output)
    archive = outside(args.archive, [root])
    entries = list(scan(root).values())
    if not entries:
        raise ValueError('The original resource directory is empty')
    for entry in entries:
        entry.update(action='original', expected_sha256=entry['source']['sha256'])
    if any('=' not in option or not option.split('=', 1)[0] for option in args.option):
        raise ValueError('Creation options must use Name=Value')
    value = dict(schema_version=1, kind=KIND, stage='extracted', complete=True, created_at=now(),
                 resource_root=str(root), archive=dict(source=file_info(archive),
                 format=args.format, options=args.option), entries=entries)
    write_new(output, value)
    return dict(manifest=str(output), original_resources=len(entries))


def merge(args):
    baseline = load_manifest(args.manifest, 'extracted')
    generated = load_manifest(args.replacements, 'generated')
    root = Path(baseline['resource_root']).resolve(strict=True)
    generated_root = Path(generated['output_root']).resolve(strict=True)
    if Path(generated['resource_root']).resolve() != root:
        raise ValueError('TTS asset_root must match the original archive extraction root')
    check_file(baseline['archive']['source'])
    check_file(generated['mapping'])
    require_tree(root, baseline['entries'])
    original = {entry['path'].casefold(): entry for entry in baseline['entries']}
    replacements = {}
    for entry in generated['entries']:
        key = entry['path'].casefold()
        if key not in original:
            raise ValueError(f'Replacement has no original archive entry: {entry["path"]}')
        source = check_file(entry['source'])
        if source != (root / entry['path']).resolve() or entry['source']['sha256'] != original[key]['source']['sha256']:
            raise ValueError(f'Replacement refers to a different original resource: {entry["path"]}')
        replacement = check_file(entry['replacement'])
        if not replacement.is_relative_to(generated_root):
            raise ValueError(f'Replacement lies outside TTS output_root: {replacement}')
        replacements[key] = entry
    stage = fresh_directory(args.staging, [root, generated_root])
    output = outside(args.output, [root, generated_root, stage])
    if output.exists():
        raise FileExistsError(output)
    entries = []
    for key, original_entry in original.items():
        replacement = replacements.get(key)
        if args.mode == 'patch' and replacement is None:
            continue
        entry = dict(original_entry)
        entry['action'] = 'replaced' if replacement else 'retained'
        if replacement:
            entry['replacement'] = replacement['replacement']
            entry['expected_sha256'] = replacement['replacement']['sha256']
        entries.append(entry)
    stage.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.gal-merge-', dir=stage.parent) as temporary:
        tree = Path(temporary) / 'resources'
        tree.mkdir()
        import shutil
        for entry in entries:
            target = tree / entry['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            info = entry.get('replacement', entry['source'])
            shutil.copy2(info['path'], target)
        require_tree(tree, entries)
        tree.rename(stage)
    value = dict(schema_version=1, kind=KIND, stage='staged', complete=True, created_at=now(),
                 resource_root=str(stage), original_root=str(root), generated_root=str(generated_root),
                 archive=baseline['archive'], mode=args.mode,
                 inputs=dict(original_manifest=file_info(args.manifest), replacements=file_info(args.replacements)),
                 entries=entries)
    write_new(output, value)
    return dict(manifest=str(output), staging=str(stage), mode=args.mode,
                replaced=len(replacements), retained=len(entries) - len(replacements), total=len(entries))


def cli(executable, arguments):
    result = subprocess.run([str(executable.resolve(strict=True)), *map(str, arguments)],
                            capture_output=True, encoding='utf-8-sig', errors='replace')
    if result.returncode:
        raise RuntimeError(f'GARbro exited with {result.returncode}: {result.stderr.strip()}')
    return result


def verify_output(value, archive, garbro, directory):
    directory = fresh_directory(directory, [value['resource_root'], value['original_root'], value['generated_root']])
    cli(garbro, ['x', '-q', '-s', '-o', directory, archive])
    report = compare_tree(directory, value['entries'])
    report.update(verified_at=now(), archive=file_info(archive), verification_directory=str(directory),
                  mode=value['mode'], format=value['archive']['format'], total=len(value['entries']),
                  replaced=sum(e['action'] == 'replaced' for e in value['entries']),
                  retained=sum(e['action'] == 'retained' for e in value['entries']),
                  game_playback='not_tested')
    return report


def pack_or_verify(args):
    value = load_manifest(args.manifest, 'staged')
    roots = [value['resource_root'], value['original_root'], value['generated_root']]
    archive = outside(args.output if args.command == 'pack' else args.archive, roots)
    report_path = outside(args.report, roots)
    directory = fresh_directory(args.verification_dir, roots)
    if report_path.exists() or report_path == archive:
        raise FileExistsError(f'Use a new report path distinct from the archive: {report_path}')
    if archive.is_relative_to(directory) or report_path.is_relative_to(directory):
        raise ValueError('Archive and report must be outside the verification directory')
    if args.command == 'pack':
        if archive.exists():
            raise FileExistsError(f'Use a new output archive: {archive}')
        check_file(value['archive']['source'])
        require_tree(value['resource_root'], value['entries'])
        arguments = ['c', '-q', '-s', '-t', value['archive']['format'], '-o', archive, '-R']
        for option in value['archive']['options']:
            arguments += ['-O', option]
        arguments.append(value['resource_root'])
        cli(args.garbro, arguments)
    try:
        report = verify_output(value, archive, args.garbro, directory)
    except Exception as error:
        report = dict(passed=False, archive=str(archive), error=str(error), game_playback='not_tested')
    report['manifest'] = file_info(args.manifest)
    write_new(report_path, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot = commands.add_parser('init', help='Snapshot a raw extracted archive; does not parse dialogue')
    snapshot.add_argument('--original-root', type=Path, required=True)
    snapshot.add_argument('--archive', type=Path, required=True)
    snapshot.add_argument('--format', required=True)
    snapshot.add_argument('-O', '--option', action='append', default=[])
    snapshot.add_argument('--manifest', type=Path, required=True)
    combine = commands.add_parser('merge', help='Merge verified TTS outputs into a fresh staging directory')
    combine.add_argument('--manifest', type=Path, required=True)
    combine.add_argument('--replacements', type=Path, required=True)
    combine.add_argument('--staging', type=Path, required=True)
    combine.add_argument('--output', type=Path, required=True)
    combine.add_argument('--mode', choices=['full', 'patch'], default='full')
    for name in ['pack', 'verify']:
        command = commands.add_parser(name)
        command.add_argument('--manifest', type=Path, required=True)
        command.add_argument('--garbro', type=Path, required=True)
        command.add_argument('--output' if name == 'pack' else '--archive', type=Path, required=True)
        command.add_argument('--verification-dir', type=Path, required=True)
        command.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(argv)
    result = init(args) if args.command == 'init' else merge(args) if args.command == 'merge' else pack_or_verify(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get('passed') is False else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
