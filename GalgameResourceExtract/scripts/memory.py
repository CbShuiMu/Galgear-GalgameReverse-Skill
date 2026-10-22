"""Per-user configuration, findings, and checkpoints for GalExtract. No extraction is executed."""
from pathlib import Path
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
import sys


def default_memory_path():
    if os.environ.get('GAL_EXTRACT_HOME'):
        return Path(os.environ['GAL_EXTRACT_HOME']).expanduser() / 'memory.json'
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'GalExtract/memory.json'
    return Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'gal-extract/memory.json'


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def load(path):
    if not Path(path).is_file():
        return dict(schema_version=1, last_project=None, projects={})
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict) or value.get('schema_version') != 1 or not isinstance(value.get('projects'), dict):
        raise ValueError('Invalid GalExtract memory schema')
    return value


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def checksum(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while chunk := handle.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def snapshot(path, with_hash=False):
    path = Path(path).expanduser().resolve(strict=True)
    stat = path.stat()
    result = dict(path=str(path), kind='directory' if path.is_dir() else 'file',
                  size=stat.st_size, mtime_ns=stat.st_mtime_ns)
    if with_hash and path.is_file():
        result['sha256'] = checksum(path)
    return result


def merge(base, patch):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def context(args, memory):
    name = args.project or memory.get('last_project')
    if name not in memory['projects']:
        raise ValueError('No matching project. Use --project NAME configure --game-root PATH --output-dir PATH first.')
    return name, memory['projects'][name]


def inspect_project(project):
    issues = []
    root = Path(project['game_root'])
    if not root.is_dir():
        issues.append(dict(scope='game_root', path=str(root), reason='missing'))
    for label, recorded in project.get('sources', {}).items():
        path = Path(recorded['path'])
        if not path.exists():
            issues.append(dict(scope='source', path=str(path), reason='missing'))
            continue
        actual = snapshot(path, 'sha256' in recorded)
        fields = ('kind', 'size', 'mtime_ns', 'sha256') if recorded['kind'] == 'file' else ('kind', 'mtime_ns')
        changed = [field for field in fields if field in recorded and actual.get(field) != recorded[field]]
        if changed:
            issues.append(dict(scope='source', path=str(path), reason='changed', fields=changed))
    for stage, checkpoint in project.get('checkpoints', {}).items():
        if checkpoint.get('status') != 'completed':
            continue
        for artifact in checkpoint.get('artifacts', []):
            path = Path(artifact['path'])
            if not path.exists():
                issues.append(dict(scope='artifact', stage=stage, path=str(path), reason='missing'))
                continue
            actual = snapshot(path, 'sha256' in artifact)
            # Directory contents can change as later stages produce more files.
            fields = ('kind', 'size', 'mtime_ns', 'sha256') if artifact['kind'] == 'file' else ('kind',)
            changed = [field for field in fields if field in artifact and actual.get(field) != artifact[field]]
            if changed:
                issues.append(dict(scope='artifact', stage=stage, path=str(path), reason='changed', fields=changed))
    return dict(passed=not issues, checked_at=now(), issues=issues,
                note='Only recorded paths are checked. Metadata-only observations do not prove byte-for-byte identity.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory', type=Path, default=default_memory_path())
    parser.add_argument('--project')
    commands = parser.add_subparsers(dest='command', required=True)
    show = commands.add_parser('memory')
    show.add_argument('--where', action='store_true')
    config = commands.add_parser('configure')
    config.add_argument('--game-root')
    config.add_argument('--output-dir')
    update = commands.add_parser('update')
    update.add_argument('--patch', type=Path, required=True)
    observe = commands.add_parser('observe')
    observe.add_argument('--source', type=Path, action='append', required=True)
    observe.add_argument('--hash', action='store_true', help='Hash source files; large archives can take time')
    checkpoint = commands.add_parser('checkpoint')
    checkpoint.add_argument('stage')
    checkpoint.add_argument('--status', choices=['pending', 'running', 'completed', 'failed', 'stopped'], required=True)
    checkpoint.add_argument('--notes')
    checkpoint.add_argument('--artifact', type=Path, action='append', default=[])
    checkpoint.add_argument('--hash', action='store_true', help='Hash artifact files')
    commands.add_parser('check')
    args = parser.parse_args(argv)
    args.memory = args.memory.expanduser().resolve()
    if args.command == 'memory' and args.where:
        print(args.memory)
        return 0
    memory = load(args.memory)
    if args.command == 'memory':
        value = context(args, memory)[1] if args.project else memory
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    if args.command == 'configure':
        name = args.project or memory.get('last_project')
        if not name:
            raise ValueError('--project is required for the first configuration')
        existing = memory['projects'].get(name, {})
        project = copy.deepcopy(existing)
        if args.game_root is not None:
            root = Path(args.game_root).expanduser().resolve(strict=True)
            if not root.is_dir():
                raise ValueError('game_root must be a directory')
            if existing.get('game_root') and str(root) != existing['game_root']:
                raise ValueError('A different game root requires a new project name so findings are not mixed')
            project['game_root'] = str(root)
        if args.output_dir is not None:
            project['output_dir'] = str(Path(args.output_dir).expanduser().resolve())
        if not project.get('game_root') or not project.get('output_dir'):
            raise ValueError('A new project requires --game-root and --output-dir')
        project['updated_at'] = now()
    else:
        name, original = context(args, memory)
        project = copy.deepcopy(original)
        if args.command == 'check':
            report = inspect_project(project)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report['passed'] else 1
        if args.command == 'update':
            patch = json.loads(args.patch.read_text(encoding='utf-8-sig'))
            if not isinstance(patch, dict):
                raise ValueError('Patch must be a JSON object')
            allowed = {'engine', 'resources', 'tools', 'artifacts', 'counts', 'unresolved', 'notes'}
            unexpected = set(patch) - allowed
            if unexpected:
                raise ValueError(f'Unsupported patch fields: {sorted(unexpected)}; use configure, observe, or checkpoint for other fields')
            project = merge(project, patch)
        elif args.command == 'observe':
            sources = project.setdefault('sources', {})
            root = Path(project['game_root'])
            for path in args.source:
                entry = snapshot(path, args.hash)
                resolved = Path(entry['path'])
                if not resolved.is_relative_to(root):
                    raise ValueError(f'Observed source must be inside game_root: {path}')
                sources[str(resolved.relative_to(root))] = entry
        elif args.command == 'checkpoint':
            artifacts = [snapshot(path, args.hash) for path in args.artifact]
            entry = dict(status=args.status, updated_at=now(), artifacts=artifacts)
            if args.notes is not None:
                entry['notes'] = args.notes
            project.setdefault('checkpoints', {})[args.stage] = entry
        project['updated_at'] = now()
    memory['projects'][name] = project
    memory['last_project'] = name
    save(args.memory, memory)
    print(json.dumps(project, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
