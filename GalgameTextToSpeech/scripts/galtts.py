"""Reusable JSON-to-Chinese-voice batch runner. Never starts a job on import."""
from pathlib import Path, PureWindowsPath, PurePosixPath
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
import traceback

from dialogue_mapping import clean_text, normalize_mapping

HERE = Path(__file__).resolve().parent


def default_memory_path():
    if os.environ.get('GAL_TTS_HOME'):
        return Path(os.environ['GAL_TTS_HOME']).expanduser() / 'memory.json'
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'GalTTS/memory.json'
    return Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'gal-tts/memory.json'


DEFAULT_MEMORY = default_memory_path()


def load_memory(path):
    if Path(path).is_file():
        return read_json(path)
    return dict(schema_version=1, last_project=None, profiles={}, projects={})


def adapter_path(profile):
    adapter = profile['adapter']
    builtins = {'builtin:index': 'index_backend.py', 'builtin:command': 'command_backend.py'}
    return HERE / builtins[adapter] if adapter in builtins else Path(adapter).resolve()


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def get_context(args):
    memory = load_memory(args.memory)
    name = args.project or memory.get('last_project')
    if name not in memory.get('projects', {}):
        raise ValueError(f'No matching project configured: {name}. Register your chosen model with profile, then use configure.')
    project = memory['projects'][name]
    profile_name = project['profile']
    profile = memory['profiles'][profile_name]
    return memory, name, project, profile


def workdir(project):
    return Path(project['output_dir']) / '.galtts'


def configure(args):
    memory = load_memory(args.memory)
    name = args.project or memory.get('last_project')
    if not name:
        raise ValueError('--project is required for the first configuration')
    project = dict(memory['projects'].get(name, {}))
    new_project = name not in memory['projects']
    for field in ('input_json', 'asset_root', 'output_dir'):
        value = getattr(args, field)
        if value is not None:
            project[field] = str(Path(value).resolve())
    if args.profile:
        project['profile'] = args.profile
    if args.nonverbal:
        project['nonverbal'] = args.nonverbal
    if args.output_layout:
        project['output_layout'] = args.output_layout
    project.setdefault('output_layout', 'relative' if new_project else 'flat')
    for field in ('input_json', 'asset_root', 'output_dir', 'profile'):
        if field not in project:
            raise ValueError(f'Missing configuration: {field}')
    if project['profile'] not in memory['profiles']:
        raise ValueError(f'Unknown profile: {project["profile"]}')
    project.setdefault('nonverbal', 'copy')
    project['updated_at'] = now()
    memory['projects'][name] = project
    memory['last_project'] = name
    atomic_json(args.memory, memory)
    print(json.dumps(project, ensure_ascii=False, indent=2))


def register_profile(args):
    memory = load_memory(args.memory)
    profile = dict(memory['profiles'].get(args.name, {}))
    for key in ('python', 'ffmpeg'):
        value = getattr(args, key)
        if value is not None:
            found = shutil.which(value) or value
            path = Path(found).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(f'{key}: {path}')
            profile[key] = str(path)
    if args.adapter is not None:
        if args.adapter in {'index', 'command'}:
            profile['adapter'] = 'builtin:' + args.adapter
        else:
            path = Path(args.adapter).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            profile['adapter'] = str(path)
    if args.settings_file is not None:
        settings = read_json(args.settings_file)
        if not isinstance(settings, dict):
            raise ValueError('The settings file must contain a JSON object')
        profile['settings'] = settings
    if args.model_revision is not None:
        profile['model_revision'] = args.model_revision
    for key in ('python', 'adapter', 'ffmpeg'):
        if key not in profile:
            raise ValueError(f'New profiles require --{key}; no model is selected automatically')
    profile.setdefault('settings', {})
    memory['profiles'][args.name] = profile
    atomic_json(args.memory, memory)
    print(json.dumps(dict(name=args.name, **profile), ensure_ascii=False, indent=2))


def safe_name(name):
    if (not isinstance(name, str) or not name or name in {'.', '..'}
            or Path(name).name != name or PureWindowsPath(name).name != name
            or ':' in name or name.endswith((' ', '.'))):
        raise ValueError(f'Unsafe audio filename: {name!r}')
    return name


def resource_path(value):
    if not isinstance(value, str) or not value or PureWindowsPath(value).drive:
        raise ValueError(f'Unsafe resource path: {value!r}')
    value = value.replace('\\', '/')
    parts = value.split('/')
    if any(p in {'', '.', '..'} or ':' in p or p.endswith((' ', '.')) for p in parts):
        raise ValueError(f'Unsafe resource path: {value!r}')
    if parts[0].casefold() == '.galtts':
        raise ValueError('The .galtts directory is reserved for batch metadata')
    return PurePosixPath(value).as_posix()


def build_plan(project, profile):
    from audio_formats import EXTENSIONS, export_args, probe
    root = Path(project['asset_root']).resolve(strict=True)
    destination = Path(project['output_dir']).resolve()
    if destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError('asset_root and output_dir must be separate, non-overlapping directories')
    layout = project.get('output_layout', 'flat')  # Preserve existing saved projects.
    if layout not in {'relative', 'flat'}:
        raise ValueError('output_layout must be relative or flat')
    occurrences = normalize_mapping(read_json(project['input_json']))
    adapter = adapter_path(profile)
    if not adapter.is_file():
        raise FileNotFoundError(adapter)
    ffmpeg = Path(project.get('ffmpeg') or profile['ffmpeg'])
    if not ffmpeg.is_file():
        raise FileNotFoundError(ffmpeg)
    identity = dict(profile=profile, adapter_sha256=sha(adapter),
                    export_version=2 if layout == 'relative' else 1, exporter_sha256=sha(HERE / 'audio_formats.py'),
                    generation=project.get('generation', {}),
                    vorbis_quality=project.get('vorbis_quality', 5))
    tasks, seen = [], {}
    for occurrence in occurrences:
        reference = occurrence['reference']
        row_index = reference['row']
        text = occurrence['text']
        nonverbal = not bool(re.search(r'[\w\u4e00-\u9fff]', text))
        if nonverbal and project.get('nonverbal', 'copy') == 'error':
            raise ValueError(f'Row {row_index}: empty/nonverbal text')
        name = safe_name(occurrence['name'])
        if Path(name).suffix.lower() not in EXTENSIONS:
            raise ValueError(f'Unsupported audio extension: {name}')
        if occurrence['path'] is None:
            candidates = [root / 'Voice' / name, root / name]
            existing = [p for p in candidates if p.is_file()]
            if len(existing) != 1:
                raise ValueError(f'Ambiguous or missing source for {name}; supply audio_paths')
            source = existing[0].resolve()
        else:
            relative = resource_path(occurrence['path'])
            source = (root / relative).resolve(strict=True)
        if not source.is_relative_to(root) or source.name != name or not source.is_file():
            raise ValueError(f'Unsafe or mismatched source: {source}')
        relative = resource_path(source.relative_to(root).as_posix())
        output_path = relative if layout == 'relative' else name
        previous = seen.get(output_path.casefold())
        if previous is not None:
            if previous['resource_path'].casefold() != relative.casefold():
                raise ValueError(f'Duplicate output path: {output_path}; use relative layout for nested resources')
            if previous['text'] != text:
                raise ValueError(f'Conflicting text for shared audio {relative}: rows {previous["row"]} and {row_index}; one resource cannot contain different lines')
            previous['references'].append(reference)
            continue
        target = destination / output_path
        if not target.resolve().is_relative_to(destination):
            raise ValueError(f'Output path escapes output_dir: {target}')
        if target.resolve() == source:
            raise ValueError(f'Output would overwrite the original: {source}')
        spec = probe(source)
        # Nonverbal entries are copied byte-for-byte and require no encoder.
        if not nonverbal:
            export_args(spec, target.suffix, ffmpeg, project.get('vorbis_quality', 5))
        source_hash = sha(source)
        fingerprint = digest(dict(source_sha256=source_hash, text=text,
                                  action='copy' if nonverbal else 'synthesize', identity=identity))
        task = dict(filename=output_path, basename=name, resource_path=relative,
                    source=str(source), source_sha256=source_hash, target=str(target), text=text,
                    row=row_index, references=[reference], nonverbal=nonverbal,
                    source_spec=spec.to_dict(), fingerprint=fingerprint)
        tasks.append(task)
        seen[output_path.casefold()] = task
    return dict(schema_version=1, created_at=now(), input_json=project['input_json'],
                input_json_sha256=sha(project['input_json']), asset_root=str(root),
                output_dir=str(destination), output_layout=layout,
                profile=project['profile'], profile_identity=digest(identity), ffmpeg=str(ffmpeg),
                total=len(tasks), total_references=len(occurrences),
                reused_references=len(occurrences) - len(tasks),
                nonverbal=sum(t['nonverbal'] for t in tasks), tasks=tasks)


def journal_entries(folder):
    entries = {}
    path = folder / 'manifest.jsonl'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                item = json.loads(line)
                if item.get('status') == 'ok':
                    entries[item['filename']] = item
            except json.JSONDecodeError:
                continue  # Ignore a partially written final line after a crash.
    return entries


def verified_existing(task, entries):
    old = entries.get(task['filename'])
    target = Path(task['target'])
    return bool(old and old['fingerprint'] == task['fingerprint'] and target.is_file()
                and sha(target) == old['output_sha256'])


def create_backend(profile):
    module_path = adapter_path(profile)
    spec = importlib.util.spec_from_file_location('galtts_selected_backend', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_backend(profile.get('settings', {}))


def audit(plan, folder, selected=None):
    from audio_formats import AudioSpec, probe, verify_match
    selected = plan['tasks'] if selected is None else selected
    entries = journal_entries(folder)
    errors = []
    for task in selected:
        try:
            if not verified_existing(task, entries):
                raise ValueError('Missing output or mismatched source/profile/output checksum')
            if sha(task['source']) != task['source_sha256']:
                raise ValueError('Source changed after preflight')
            entry = entries[task['filename']]
            if entry['action'] == 'copied_nonverbal':
                if sha(task['source']) != sha(task['target']):
                    raise ValueError('Copied nonverbal audio differs')
            else:
                verify_match(AudioSpec(**task['source_spec']), probe(task['target']))
        except Exception as error:
            errors.append(dict(filename=task['filename'], error=str(error)))
    expected_names = {t['filename'].casefold() for t in plan['tasks']}
    from audio_formats import EXTENSIONS
    destination = Path(plan['output_dir'])
    unexpected = [p.relative_to(destination).as_posix() for p in destination.rglob('*')
                  if p.is_file() and p.relative_to(destination).parts[0].casefold() != '.galtts'
                  and p.suffix.lower() in EXTENSIONS
                  and p.relative_to(destination).as_posix().casefold() not in expected_names]
    report = dict(passed=not errors and not unexpected, audited_at=now(),
                  checked=len(selected), total=plan['total'], full_batch=len(selected) == plan['total'],
                  errors=errors, unexpected_files=unexpected)
    atomic_json(folder / 'audit.json', report)
    handoff = dict(schema_version=1, kind='gal-resource-manifest', stage='generated',
                   complete=report['passed'] and report['full_batch'], created_at=now(),
                   resource_root=plan['asset_root'], output_root=plan['output_dir'],
                   mapping=dict(path=plan['input_json'], sha256=plan['input_json_sha256']),
                   profile_identity=plan['profile_identity'], entries=[])
    if handoff['complete']:
        for task in plan['tasks']:
            result = entries[task['filename']]
            handoff['entries'].append(dict(path=task['resource_path'], fingerprint=task['fingerprint'],
                references=task['references'],
                action=result['action'], source=dict(path=task['source'], sha256=task['source_sha256'],
                    size=Path(task['source']).stat().st_size),
                replacement=dict(path=task['target'], sha256=result['output_sha256'],
                    size=Path(task['target']).stat().st_size, audio_spec=result['output_spec'])))
    atomic_json(folder / 'resources.json', handoff)
    return report


def execute(args, memory, name, project, profile, plan):
    from audio_formats import AudioSpec, encode_like, probe, reference_wav, validate_signal
    from filelock import FileLock
    folder = workdir(project)
    folder.mkdir(parents=True, exist_ok=True)
    selected = plan['tasks'][:args.limit] if args.limit else plan['tasks']
    with FileLock(str(folder / 'batch.lock'), timeout=0):
        stop = folder / 'STOP_AFTER_CURRENT'
        if stop.exists() and not args.resume:
            raise ValueError('Batch is stopped. Use --resume only after a new user start/resume request.')
        if args.resume:
            stop.unlink(missing_ok=True)
        entries = journal_entries(folder)
        # Protect existing deliveries, including outputs produced by other tools.
        conflicts = [t['filename'] for t in selected if Path(t['target']).exists()
                     and not verified_existing(t, entries)]
        if conflicts:
            raise ValueError(f'Existing outputs are not verified for this configuration; select a new output_dir: {conflicts[:8]}')
        from audio_formats import EXTENSIONS
        expected = {t['filename'].casefold() for t in plan['tasks']}
        extra = [p.relative_to(Path(plan['output_dir'])).as_posix()
                 for p in Path(plan['output_dir']).rglob('*') if p.is_file()
                 and p.relative_to(Path(plan['output_dir'])).parts[0].casefold() != '.galtts'
                 and p.suffix.lower() in EXTENSIONS
                 and p.relative_to(Path(plan['output_dir'])).as_posix().casefold() not in expected]
        if extra:
            raise ValueError(f'Unexpected audio outputs; select a clean output_dir: {extra[:8]}')
        atomic_json(folder / 'resources.json', dict(schema_version=1, kind='gal-resource-manifest',
                    stage='generated', complete=False, entries=[]))
        atomic_json(folder / 'plan.json', plan)
        atomic_json(folder / 'source.json', read_json(project['input_json']))
        started = time.monotonic()
        completed = 0
        failed = []
        state = {}

        def progress(status, current=None):
            state.update(status=status, updated_at=now(), project=name, profile=project['profile'],
                         total=plan['total'], selected=len(selected), completed=completed,
                         failed=len(failed), current=current, output_dir=project['output_dir'],
                         elapsed_seconds=round(time.monotonic() - started, 1))
            atomic_json(folder / 'progress.json', state)

        backend = None
        progress('running')
        log = (folder / 'engine.log').open('a', encoding='utf-8', buffering=1)
        try:
            with (folder / 'manifest.jsonl').open('a', encoding='utf-8', buffering=1) as journal:
                for task in selected:
                    if stop.exists():
                        progress('stopped')
                        break
                    if verified_existing(task, entries):
                        completed += 1
                        progress('running', task['filename'])
                        continue
                    progress('running', task['filename'])
                    entry = dict(filename=task['filename'], fingerprint=task['fingerprint'],
                                 text=task['text'], started_at=now())
                    fatal_backend_error = False
                    try:
                        target = Path(task['target'])
                        if sha(task['source']) != task['source_sha256']:
                            raise ValueError('Source changed after preflight')
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if task['nonverbal']:
                            temporary = target.with_name(target.stem + '.partial' + target.suffix)
                            shutil.copyfile(task['source'], temporary)
                            temporary.replace(target)
                            action = 'copied_nonverbal'
                        else:
                            if backend is None:
                                progress('loading_model', task['filename'])
                                with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                                    backend = create_backend(profile)
                                progress('running', task['filename'])
                            reference = reference_wav(task['source'], folder / 'references' / (task['filename'] + '.wav'), plan['ffmpeg'])
                            wav = folder / 'wav' / (task['filename'] + '.wav')
                            wav.parent.mkdir(parents=True, exist_ok=True)
                            last_error = None
                            for attempt in range(project.get('retries', 2) + 1):
                                try:
                                    wav.unlink(missing_ok=True)
                                    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                                        backend.synthesize(text=task['text'], reference_audio=str(reference),
                                                           output_wav=str(wav), language='zh',
                                                           seed=(int(task['fingerprint'][:8], 16) + attempt) % (2**31),
                                                           options=project.get('generation', {}))
                                    validate_signal(wav, plan['ffmpeg'])
                                    if probe(wav).seconds > project.get('max_output_seconds', 180):
                                        raise ValueError('Generated audio exceeds max_output_seconds')
                                    last_error = None
                                    break
                                except Exception as error:
                                    last_error = error
                                    log.write(f'\n{task["filename"]} attempt {attempt+1}: {error}\n')
                            if last_error:
                                raise last_error
                            encode_like(wav, target, AudioSpec(**task['source_spec']), plan['ffmpeg'],
                                        project.get('vorbis_quality', 5))
                            action = 'generated'
                        entry.update(status='ok', action=action, output_sha256=sha(target),
                                     output_spec=probe(target).to_dict())
                        completed += 1
                        entries[task['filename']] = entry
                    except Exception as error:
                        entry.update(status='failed', error=f'{type(error).__name__}: {error}')
                        failed.append(entry)
                        fatal_backend_error = backend is None and not task['nonverbal']
                        traceback.print_exc(file=log)
                    entry['finished_at'] = now()
                    journal.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    progress('backend_failed' if fatal_backend_error else 'running', task['filename'])
                    print(json.dumps(dict(completed=completed, selected=len(selected), filename=task['filename'],
                                          status=entry['status'], failed=len(failed)), ensure_ascii=False), flush=True)
                    if fatal_backend_error:
                        break  # Do not try to reload a broken/missing model for every remaining line.
                else:
                    progress('completed_with_errors' if failed else
                             'completed' if len(selected) == plan['total'] else 'sample_completed')
            if state['status'] in {'completed', 'sample_completed'}:
                report = audit(plan, folder, selected)
                if not report['passed']:
                    progress('audit_failed')
        except BaseException:
            progress('interrupted')
            raise
        finally:
            if backend is not None and hasattr(backend, 'close'):
                try:
                    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                        backend.close()
                except Exception:
                    traceback.print_exc(file=log)
            log.close()
            state['failures'] = failed
            atomic_json(folder / 'report.json', state)
            # Preserve configuration edits made while a long batch was running.
            latest_memory = load_memory(args.memory)
            if name in latest_memory.get('projects', {}):
                latest_memory['projects'][name]['last_status'] = state['status']
                latest_memory['projects'][name]['last_run_at'] = now()
                latest_memory['projects'][name]['last_run_output_dir'] = project['output_dir']
            atomic_json(args.memory, latest_memory)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0 if state['status'] in {'completed', 'sample_completed', 'stopped'} else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory', type=Path, default=DEFAULT_MEMORY)
    parser.add_argument('--project')
    commands = parser.add_subparsers(dest='command', required=True)
    memory_command = commands.add_parser('memory')
    memory_command.add_argument('--where', action='store_true', help='Show the per-user state path without writing a file')
    profile = commands.add_parser('profile', help='Register or update a user-selected model; does not load it')
    profile.add_argument('name')
    profile.add_argument('--adapter', help='index, command, or a Python adapter file')
    profile.add_argument('--python')
    profile.add_argument('--ffmpeg')
    profile.add_argument('--settings-file', type=Path)
    profile.add_argument('--model-revision')
    config = commands.add_parser('configure')
    config.add_argument('--input-json')
    config.add_argument('--asset-root')
    config.add_argument('--output-dir')
    config.add_argument('--profile')
    config.add_argument('--nonverbal', choices=['copy', 'error'])
    config.add_argument('--output-layout', choices=['relative', 'flat'])
    commands.add_parser('plan')
    run = commands.add_parser('run')
    run.add_argument('--resume', action='store_true')
    run.add_argument('--limit', type=int)
    commands.add_parser('stop')
    commands.add_parser('status')
    commands.add_parser('audit')
    commands.add_parser('handoff', help='Audit the full batch and export .galtts/resources.json without loading a model')
    args = parser.parse_args(argv)
    if args.command == 'memory':
        if args.where:
            print(args.memory.expanduser().resolve())
        else:
            print(json.dumps(load_memory(args.memory), ensure_ascii=False, indent=2))
        return 0
    if args.command == 'profile':
        register_profile(args)
        return 0
    if args.command == 'configure':
        configure(args)
        return 0
    memory, name, project, profile = get_context(args)
    folder = workdir(project)
    if args.command == 'stop':
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'STOP_AFTER_CURRENT').write_text('User requested stop.\n', encoding='utf-8')
        print('Stop requested; the current file may finish before the worker exits.')
        return 0
    if args.command == 'status':
        path = folder / 'progress.json'
        print(json.dumps(read_json(path) if path.exists() else
                         dict(status=project.get('last_status', 'not_started'), output_dir=project['output_dir']),
                         ensure_ascii=False, indent=2))
        return 0
    if args.command == 'run' and args.limit is not None and args.limit <= 0:
        raise ValueError('--limit must be positive')
    plan = build_plan(project, profile)
    if args.command == 'plan':
        folder.mkdir(parents=True, exist_ok=True)
        atomic_json(folder / 'preflight.json', plan)
        entries = journal_entries(folder)
        conflicts = [t['filename'] for t in plan['tasks'] if Path(t['target']).exists()
                     and not verified_existing(t, entries)]
        print(json.dumps(dict(total=plan['total'], total_references=plan['total_references'],
                              reused_references=plan['reused_references'],
                              nonverbal=plan['nonverbal'], output_dir=plan['output_dir'],
                              profile=plan['profile'], formats=sorted({t['source_spec']['codec'] for t in plan['tasks']}),
                              existing_unverified_outputs=len(conflicts), preflight=str(folder/'preflight.json')),
                         ensure_ascii=False, indent=2))
        return 0
    if args.command in {'audit', 'handoff'}:
        report = audit(plan, folder)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['passed'] else 1
    return execute(args, memory, name, project, profile, plan)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
