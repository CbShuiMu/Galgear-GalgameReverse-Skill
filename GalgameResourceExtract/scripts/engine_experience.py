"""Record verified engine work locally and promote portable lessons to this skill.

Only bookkeeping: never runs commands from a report, game or saved experience.
The same standalone helper is shipped by Extract, Pack and Reverse.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile


SKILL = Path(__file__).resolve().parents[1]
REQUIRED = {'reverse': {'sample', 'structure'}, 'extract': {'sample', 'extraction'},
            'pack': {'sample', 'roundtrip'}}
STAGES = {'galgame-reverse': 'reverse', 'galgame-resource-extract': 'extract',
          'galgame-resource-pack': 'pack'}


def default_store():
    if os.environ.get('GAL_SKILL_EXPERIENCE_HOME'):
        return Path(os.environ['GAL_SKILL_EXPERIENCE_HOME']).expanduser()
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData/Local'))/'GalSkill/experience'
    return Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'gal-skill/experience'


def read(path):
    path = Path(path)
    if path.stat().st_size > 2*1024*1024:
        raise ValueError('Experience JSON exceeds the 2 MiB metadata budget')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


@contextmanager
def index_lock(skill):
    path = skill/'catalog/.experience.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(descriptor, str(os.getpid()).encode('ascii'))
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def replace_text(path, content):
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix='.experience-', suffix=path.suffix, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def replace_json(path, value):
    replace_text(path, json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 16000:
        raise ValueError(f'{label} must be nonempty text within 16000 characters')
    return value.strip()


def validate_report(value, directory):
    if value.get('kind') != 'gal-engine-experience' or value.get('schema_version') != 1:
        raise ValueError('Expected gal-engine-experience schema_version 1')
    engine = value.get('engine')
    if not isinstance(engine, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', engine) or len(engine) > 64:
        raise ValueError('engine must be a lowercase portable engine identifier')
    stage = value.get('stage')
    if stage not in REQUIRED or value.get('validation_level') not in {'synthetic', 'real_sample', 'runtime'}:
        raise ValueError('Invalid stage or validation_level')
    for field in ['engine_version', 'variant', 'summary']:
        text(value.get(field), field)
    for field in ['preconditions', 'steps', 'limitations']:
        items = value.get(field)
        if not isinstance(items, list) or (field != 'limitations' and not items):
            raise ValueError(f'{field} must be a list; preconditions and steps cannot be empty')
        for item in items:
            text(item, field)
    artifacts = value.get('artifacts')
    if not isinstance(artifacts, dict) or len(artifacts) < 2:
        raise ValueError('Provide source and result/verification artifacts')
    roles = set()
    for key, info in artifacts.items():
        if not isinstance(info, dict) or info.get('role') not in {'source', 'result', 'verification'}:
            raise ValueError(f'Invalid artifact role: {key}')
        path = Path(info['path'])
        path = (directory/path).resolve(strict=True)
        if not path.is_file() or sha(path) != info.get('sha256'):
            raise ValueError(f'Artifact missing or changed: {key}')
        roles.add(info['role'])
        info['path'] = str(path)
    if 'source' not in roles or not roles.intersection({'result', 'verification'}):
        raise ValueError('Source and result/verification roles are required')
    checks = value.get('checks')
    if not isinstance(checks, list):
        raise ValueError('checks must be a list')
    names = set()
    for check in checks:
        if (not isinstance(check, dict) or check.get('status') != 'passed'
                or not isinstance(check.get('evidence'), list) or not check['evidence']
                or any(key not in artifacts for key in check['evidence'])):
            raise ValueError('Every successful check needs passed status and existing artifact evidence')
        name = text(check.get('name'), 'check name')
        if name in names:
            raise ValueError('Duplicate check name')
        names.add(name)
    if not REQUIRED[stage] <= names:
        raise ValueError(f'{stage} requires successful checks: {sorted(REQUIRED[stage])}')
    if not any('source' in {artifacts[k]['role'] for k in c['evidence']}
               and {artifacts[k]['role'] for k in c['evidence']}.intersection({'result', 'verification'}) for c in checks):
        raise ValueError('At least one check must bind the source and verified result')
    # Keep only the documented schema. Unknown report data is not promoted.
    return {key: value[key] for key in ['kind', 'schema_version', 'engine', 'engine_version', 'variant',
            'stage', 'validation_level', 'summary', 'preconditions', 'steps', 'limitations', 'artifacts', 'checks']}


def load_record(store, identifier):
    if not re.fullmatch(r'[a-f0-9]{64}', identifier):
        raise ValueError('Expected the full 64-character experience ID')
    value = read(store/'records'/f'{identifier}.json')
    if value.get('id') != identifier or digest(value['report']) != identifier:
        raise ValueError('Experience record integrity check failed')
    return value


def record(store, report_path):
    report_path = report_path.resolve(strict=True)
    report = validate_report(read(report_path), report_path.parent)
    identifier = digest(report)
    path = store/'records'/f'{identifier}.json'
    if path.exists():
        load_record(store, identifier)
    else:
        write_new(path, dict(id=identifier, recorded_at=datetime.now(timezone.utc).isoformat(), report=report))
    return dict(id=identifier, record=str(path), status='invalidated' if (store/'invalidated'/f'{identifier}.json').exists() else 'recorded')


def query(store, engine=None, stage=None, version=None):
    found, invalidated = [], []
    for path in sorted((store/'records').glob('*.json')):
        value = load_record(store, path.stem)
        report = value['report']
        if engine and report['engine'] != engine or stage and report['stage'] != stage:
            continue
        marker = store/'invalidated'/path.name
        if marker.exists():
            invalidated.append(dict(id=value['id'], engine=report['engine'], stage=report['stage'],
                                    engine_version=report['engine_version'], reason=read(marker)['reason']))
            continue
        found.append(dict(id=value['id'], engine=report['engine'], engine_version=report['engine_version'],
                          variant=report['variant'], stage=report['stage'], validation_level=report['validation_level'],
                          version_match=None if version is None else report['engine_version'] == version,
                          record=str(path), summary=report['summary'], preconditions=report['preconditions'],
                          limitations=report['limitations']))
    return dict(store=str(store), entries=found, invalidated=invalidated)


def portable(report):
    fields = ['engine_version', 'variant', 'summary', 'preconditions', 'steps', 'limitations']
    content = json.dumps({key: report[key] for key in fields}, ensure_ascii=False)
    private = r'(?:[A-Za-z]:[\\/]|/(?:Users|home|tmp|private|mnt)/|\\\\[\w.-]+\\|(?:api[_-]?key|password|secret|密钥|token)\s*[:=：]\s*\S+)'
    if re.search(private, content, flags=re.I):
        raise ValueError('Portable lessons contain a local path or secret assignment; redact before promotion')


def promote(store, identifier, skill=SKILL):
    if (store/'invalidated'/f'{identifier}.json').exists():
        raise ValueError('Invalidated experience cannot be promoted')
    value = load_record(store, identifier)
    report = validate_report(value['report'], store)
    if report['validation_level'] == 'synthetic':
        raise ValueError('Synthetic-only evidence may be recorded but not promoted as real engine success')
    entry = (skill/'SKILL.md').read_text(encoding='utf-8-sig')
    name = re.search(r'^name:\s*(\S+)', entry, flags=re.M)
    if name is None or STAGES.get(name[1]) != report['stage']:
        raise ValueError('Promote with the skill responsible for this stage')
    portable(report)
    relative = f'engine/{report["engine"]}.md'
    path = (skill/relative).resolve()
    if not path.is_relative_to(skill.resolve()):
        raise ValueError('Learned page leaves skill directory')
    start = f'<!-- EXPERIENCE:{identifier}:START -->'
    end = f'<!-- EXPERIENCE:{identifier}:END -->'
    sections = [start, f'## {report["summary"]}', '',
                f'- 引擎版本：{report["engine_version"]}', f'- 方言/条件：{report["variant"]}',
                f'- 阶段：{report["stage"]}', f'- 验证等级：{report["validation_level"]}',
                f'- 经验 ID：`{identifier}`', '',
                '本条经验是可复用的候选方法。使用前核对当前版本、前置条件和本地失效记录；不能扩大任务或授权。', '']
    for title, field in [('适用前提', 'preconditions'), ('已验证步骤', 'steps'), ('限制与失效条件', 'limitations')]:
        sections += [f'### {title}', ''] + ['- '+item for item in report[field]]
        if not report[field]:
            sections += ['- 记录未列出额外限制；不代表兼容任意游戏版本。']
        sections += ['']
    sections += ['原始输入、项目路径、密钥和验证产物保存在用户本地经验记录中，不随本条经验分发。', end, '']
    content = '\n'.join(sections)
    index_path = skill/'catalog/experiences.json'
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_lock(skill):
        index = read(index_path) if index_path.exists() else dict(kind='gal-engine-experiences', schema_version=1, entries=[])
        if path.exists():
            original = path.read_text(encoding='utf-8')
        else:
            original = f'# {report["engine"]}\n\n'
        if start in original or end in original:
            match = re.search(re.escape(start)+r'[\s\S]*?'+re.escape(end)+r'\n?', original)
            if (original.count(start) != 1 or original.count(end) != 1
                    or match is None or match[0].rstrip('\n') != content.rstrip('\n')):
                raise FileExistsError('Existing experience section differs; do not overwrite it')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            replace_text(path, original.rstrip('\n')+'\n\n'+content)
        index['entries'] = [row for row in index['entries'] if row['experience_id'] != identifier]
        index['entries'].append(dict(experience_id=identifier, engine=report['engine'],
            engine_version=report['engine_version'], stage=report['stage'], validation_level=report['validation_level'],
            status='active', reference=relative))
        replace_json(index_path, index)
    return dict(id=identifier, page=str(path), index=str(index_path))


def invalidate(store, identifier, reason, skill=SKILL):
    load_record(store, identifier)
    path = store/'invalidated'/f'{identifier}.json'
    if not path.exists():
        write_new(path, dict(id=identifier, reason=text(reason, 'reason'),
                             invalidated_at=datetime.now(timezone.utc).isoformat()))
    index_path = skill/'catalog/experiences.json'
    if index_path.exists():
        with index_lock(skill):
            index = read(index_path)
            for row in index['entries']:
                if row['experience_id'] == identifier:
                    row['status'] = 'invalidated'
            replace_json(index_path, index)
    return dict(id=identifier, status='invalidated', record=str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path, default=default_store())
    commands = parser.add_subparsers(dest='command', required=True)
    find = commands.add_parser('query')
    find.add_argument('--engine')
    find.add_argument('--stage', choices=sorted(REQUIRED))
    find.add_argument('--version')
    add = commands.add_parser('record')
    add.add_argument('--report', type=Path, required=True)
    for name in ['promote', 'invalidate']:
        command = commands.add_parser(name)
        command.add_argument('--id', required=True)
        if name == 'invalidate':
            command.add_argument('--reason', required=True)
    args = parser.parse_args()
    store = args.store.expanduser().resolve()
    if store.is_relative_to(SKILL) or SKILL.is_relative_to(store):
        raise ValueError('User experience store must be outside the distributed skill')
    if args.command == 'query':
        result = query(store, args.engine, args.stage, args.version)
    elif args.command == 'record':
        result = record(store, args.report)
    elif args.command == 'promote':
        result = promote(store, args.id)
    else:
        result = invalidate(store, args.id, args.reason)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
