"""Integration checks with synthetic audio; no TTS model or GPU is started."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

from audio_formats import encode_like, ffmpeg_run, probe, verify_match
from galtts import build_plan, read_json, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, required=True)
    args = parser.parse_args()
    ffmpeg = args.ffmpeg.resolve()
    runner = Path(__file__).with_name('galtts.py')
    with tempfile.TemporaryDirectory(prefix='galtts-check-') as temporary:
        root = Path(temporary)
        assets = root / 'assets'
        voice = assets / 'Voice'
        voice.mkdir(parents=True)
        output = root / '中文输出'
        source = root / 'tone.wav'
        samples = np.sin(2 * np.pi * 330 * np.arange(22050) / 44100).astype('float32') * 0.2
        sf.write(source, samples, 44100, subtype='PCM_16')
        cases = [
            ('PCM16.WAV', ['-c:a', 'pcm_s16le']),
            ('pcm24.wav', ['-c:a', 'pcm_s24le']),
            ('float.wav', ['-c:a', 'pcm_f32le']),
            ('mono.flac', ['-c:a', 'flac', '-sample_fmt', 's16']),
            ('stereo24.flac', ['-c:a', 'flac', '-ac', '2', '-sample_fmt', 's32', '-bits_per_raw_sample', '24']),
            ('台词.ogg', ['-c:a', 'libvorbis', '-q:a', '5']),
            ('opus.ogg', ['-c:a', 'libopus', '-ar', '48000']),
            ('voice.opus', ['-c:a', 'libopus', '-ar', '48000']),
            ('voice.mp3', ['-c:a', 'libmp3lame', '-q:a', '2']),
            ('aac.m4a', ['-c:a', 'aac']),
            ('lossless.m4a', ['-c:a', 'alac', '-sample_fmt', 's16p']),
            ('voice.aac', ['-c:a', 'aac']),
            ('voice.aiff', ['-c:a', 'pcm_s24be']),
            ('voice.wma', ['-c:a', 'wmav2']),
            ('voice.webm', ['-c:a', 'libopus', '-ar', '48000']),
        ]
        rows = []
        for name, options in cases:
            original = voice / name
            ffmpeg_run(ffmpeg, ['-y', '-i', str(source), *options, str(original)])
            spec = probe(original)
            exported = root / 'encoding' / name
            encode_like(source, exported, spec, ffmpeg)
            verify_match(spec, probe(exported))
            rows.append(dict(chinese_text='这是一条测试台词。', audio_files=[name], audio_paths=['Voice/' + name]))
        nonverbal = voice / 'nonverbal.ogg'
        nonverbal.write_bytes((voice / '台词.ogg').read_bytes())
        rows.append(dict(chinese_text='……', audio_files=[nonverbal.name], audio_paths=['Voice/' + nonverbal.name]))
        mapping = assets / 'mapping.json'
        mapping.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
        adapter = root / 'fake_backend.py'
        adapter.write_text('''from pathlib import Path
import numpy as np
import soundfile as sf
class Backend:
    def __init__(self, settings):
        self.settings=settings
        with Path(settings['counter']).open('a') as log: log.write('loaded\\n')
    def synthesize(self, *, text, reference_audio, output_wav, language, seed, options):
        assert text and language=='zh' and Path(reference_audio).is_file()
        sf.write(output_wav, np.sin(2*np.pi*440*np.arange(8000)/16000)*0.2,16000,subtype='PCM_16')
        if self.settings.get('stop_marker'):
            Path(self.settings['stop_marker']).write_text('test stop')
def create_backend(settings): return Backend(settings)
''', encoding='utf-8')
        memory_file = root / 'memory.json'
        counter = root / 'counter.txt'

        def cli(*arguments, expected=0):
            result = subprocess.run([sys.executable, str(runner), '--memory', str(memory_file),
                                     '--project', 'test', *arguments], capture_output=True, text=True,
                                    encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'})
            if result.returncode != expected:
                raise AssertionError(f'{arguments}: {result.returncode}\n{result.stdout}\n{result.stderr}')
            return result

        empty = json.loads(cli('memory').stdout)
        assert empty['profiles'] == {} and empty['projects'] == {} and empty['last_project'] is None
        assert not memory_file.exists(), 'Inspecting fresh state must not write anything'
        assert Path(cli('memory', '--where').stdout.strip()) == memory_file.resolve()
        cli('plan', expected=1)
        cli('profile', 'incomplete', expected=1)
        settings_file = root / 'backend-settings.json'
        settings_file.write_text(json.dumps(dict(counter=str(counter))), encoding='utf-8')
        cli('profile', 'test', '--python', sys.executable, '--ffmpeg', str(ffmpeg),
            '--adapter', str(adapter), '--settings-file', str(settings_file))
        assert read_json(memory_file)['last_project'] is None, 'Registering a model must not select a project'
        cli('profile', 'portable-command', '--python', sys.executable, '--ffmpeg', str(ffmpeg), '--adapter', 'command')
        assert read_json(memory_file)['profiles']['portable-command']['adapter'] == 'builtin:command'
        cli('profile', 'test', '--model-revision', 'synthetic-test-v1')
        assert read_json(memory_file)['profiles']['test']['settings']['counter'] == str(counter)
        assert not counter.exists(), 'Profile setup must not load any model'
        # A fresh user must not inherit either the author's state or another user's choices.
        isolated_home = root / 'another-user-state'
        isolated = subprocess.run([sys.executable, str(runner), 'memory'], capture_output=True,
                                 text=True, encoding='utf-8', check=True,
                                 env={**os.environ, 'GAL_TTS_HOME': str(isolated_home), 'PYTHONUTF8': '1'})
        assert json.loads(isolated.stdout)['profiles'] == {}
        assert not isolated_home.exists()
        # Built-in adapter IDs resolve relative to a relocated copy of the skill.
        relocated = root / 'relocated-skill'
        shutil.copytree(runner.parent, relocated, ignore=shutil.ignore_patterns('__pycache__'))
        resolution = subprocess.run([sys.executable, '-c',
            "from galtts import adapter_path; print(adapter_path({'adapter':'builtin:command'}))"],
            cwd=relocated, capture_output=True, text=True, encoding='utf-8', check=True)
        assert Path(resolution.stdout.strip()) == relocated / 'command_backend.py'

        cli('configure', '--input-json', str(mapping), '--asset-root', str(assets),
            '--output-dir', str(output), '--profile', 'test', '--output-layout', 'flat')
        assert read_json(memory_file)['projects']['test']['output_dir'] == str(output.resolve())
        cli('plan')
        assert not counter.exists(), 'Preflight must not load any model'
        cli('run', '--limit', '2')
        assert read_json(output / '.galtts/progress.json')['status'] == 'sample_completed'
        cli('audit', expected=1)
        before = sha(output / cases[0][0])
        cli('run')
        assert sha(output / cases[0][0]) == before, 'Verified output was regenerated'
        assert counter.read_text().count('loaded') == 2, 'Model must be loaded only once per run'
        assert (output / nonverbal.name).read_bytes() == nonverbal.read_bytes()
        cli('audit')
        assert read_json(output / '.galtts/audit.json')['full_batch'] is True
        cli('stop')
        cli('run', expected=1)
        cli('run', '--resume')
        assert counter.read_text().count('loaded') == 2, 'A verified resume should not load the model'

        project = read_json(memory_file)['projects']['test']
        profile = read_json(memory_file)['profiles']['test']
        def rejected(changed_rows):
            saved = mapping.read_bytes()
            mapping.write_text(json.dumps(changed_rows, ensure_ascii=False), encoding='utf-8')
            try:
                try:
                    build_plan(project, profile)
                except (ValueError, FileNotFoundError):
                    return
                raise AssertionError('Invalid mapping was accepted')
            finally:
                mapping.write_bytes(saved)

        saved = mapping.read_bytes()
        mapping.write_text(json.dumps([rows[0], rows[0]]), encoding='utf-8')
        shared = build_plan(project, profile)
        assert shared['total'] == 1 and shared['total_references'] == 2
        assert len(shared['tasks'][0]['references']) == 2
        mapping.write_bytes(saved)
        rejected([rows[0], dict(rows[0], chinese_text='共享音频的冲突文本。')])
        rejected([dict(rows[0], audio_files=['../escaped.wav'])])
        rejected([dict(rows[0], audio_paths=['../../tone.wav'])])
        rejected([dict(rows[0], audio_paths=[])])
        rejected([dict(audio_files=['PCM16.WAV'], audio_paths=['Voice/PCM16.WAV'])])
        disguised = voice / 'disguised.ogg'
        disguised.write_bytes(source.read_bytes())
        rejected([dict(chinese_text='测试。', audio_files=[disguised.name], audio_paths=['Voice/' + disguised.name])])
        disguised.unlink()

        # Changed text and generation settings must not reuse or overwrite an existing delivery.
        rows[0]['chinese_text'] = '已经修改的台词。'
        mapping.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
        cli('run', expected=1)
        assert sha(output / cases[0][0]) == before
        rows[0]['chinese_text'] = '这是一条测试台词。'
        mapping.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
        memory = read_json(memory_file)
        memory['projects']['test']['generation'] = {'temperature': 0.6}
        memory_file.write_text(json.dumps(memory), encoding='utf-8')
        cli('run', expected=1)
        memory['projects']['test'].pop('generation')
        memory_file.write_text(json.dumps(memory), encoding='utf-8')

        # Exercise stop during synthesis, allowing exactly the current file to finish.
        second_output = root / 'stopped-output'
        cli('configure', '--output-dir', str(second_output))
        memory = read_json(memory_file)
        memory['profiles']['test']['settings']['stop_marker'] = str(second_output / '.galtts/STOP_AFTER_CURRENT')
        memory_file.write_text(json.dumps(memory), encoding='utf-8')
        cli('run')
        state = read_json(second_output / '.galtts/progress.json')
        assert state['status'] == 'stopped' and state['completed'] == 1

        # Exercise the generic command adapter with the same JSON request contract.
        command_client = root / 'client.py'
        command_client.write_text('''import json,sys,shutil
from pathlib import Path
request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert request['text']=='命令接口测试。'
shutil.copyfile(request['reference_audio'],request['output_wav'])
''', encoding='utf-8')
        from command_backend import create_backend
        bridge = create_backend(dict(argv=[sys.executable, str(command_client), '{request_json}']))
        command_output = root / 'command.wav'
        bridge.synthesize(text='命令接口测试。', reference_audio=str(source), output_wav=str(command_output),
                          language='zh', seed=1, options={})
        assert sha(command_output) == sha(source)

        broken = root / 'broken_backend.py'
        broken_counter = root / 'broken_counter.txt'
        broken.write_text('''from pathlib import Path
def create_backend(settings):
    with Path(settings['counter']).open('a') as log: log.write('load attempt\\n')
    raise RuntimeError('model unavailable')
''', encoding='utf-8')
        memory = read_json(memory_file)
        memory['profiles']['test']['adapter'] = str(broken)
        memory['profiles']['test']['settings'] = {'counter': str(broken_counter)}
        memory_file.write_text(json.dumps(memory), encoding='utf-8')
        broken_output = root / 'broken-output'
        cli('configure', '--output-dir', str(broken_output))
        cli('run', expected=1)
        broken_state = read_json(broken_output / '.galtts/progress.json')
        assert broken_state['status'] == 'backend_failed' and broken_state['failed'] == 1
        assert broken_counter.read_text().count('load attempt') == 1
        print(json.dumps(dict(passed=True, format_cases=len(cases),
                              pipeline_tasks=len(rows), used_gpu=False,
                              checks=['format/codec/rate/channel/bit-depth preservation',
                                      'fresh setup without a default model or project',
                                      'per-user state isolation and relocated built-in adapters',
                                      'profile registration and partial updates without model loads',
                                      'configure persistence', 'preflight without model load',
                                      'sample versus full audit', 'checksum resume', 'stop/resume',
                                      'duplicate/traversal/mismatch rejection',
                                      'text/parameter fingerprint invalidation',
                                      'nonverbal exact copy', 'generic command adapter',
                                      'broken backend fails once without repeated model loads']), indent=2))


if __name__ == '__main__':
    main()
