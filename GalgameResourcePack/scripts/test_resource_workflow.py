"""Exercise raw extraction -> TTS adapter -> merge -> pack -> hash verification.

Uses synthetic audio and a fake backend in temporary directories, never a real model.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import wave


ROOT = Path(__file__).resolve().parents[2]
TTS = ROOT / 'GalgameTextToSpeech/scripts/galtts.py'
WORKFLOW = Path(__file__).with_name('resource_workflow.py')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, required=True)
    parser.add_argument('--garbro', type=Path, default=ROOT / 'GalgameResourcePack/tools/GARbro-cli/GARbro.Console.exe')
    args = parser.parse_args()
    checks = []
    with tempfile.TemporaryDirectory(prefix='gal-resource-workflow-') as temporary:
        workspace = Path(temporary)

        def call(executable, arguments, success=True):
            result = subprocess.run([str(executable), *map(str, arguments)], capture_output=True,
                                    encoding='utf-8-sig', errors='replace', timeout=60,
                                    env={**os.environ, 'PYTHONUTF8': '1'})
            assert (result.returncode == 0) == success, (arguments, result.stdout, result.stderr)
            return result

        def workflow(*arguments, success=True):
            return call(sys.executable, [WORKFLOW, *arguments], success)

        for tag in ['ZIP', 'XP3']:
            base = workspace / tag
            base.mkdir()
            seed = base / 'original-files'
            for folder in ['Voice/char_a', 'Voice/char_b']:
                (seed / folder).mkdir(parents=True)
                with wave.open(str(seed / folder / '001.wav'), 'wb') as stream:
                    stream.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
                    stream.writeframes(b''.join(struct.pack('<h', int(4000 * math.sin(i * 0.1))) for i in range(4400)))
            (seed / 'scripts').mkdir()
            (seed / 'scripts/start.tjs').write_bytes(b'unchanged script\r\n')
            (seed / 'Voice/retained.dat').write_bytes(b'unmapped resource must survive')
            archive = base / ('original.' + tag.lower())
            call(args.garbro, ['c', '-q', '-t', tag, '-o', archive, '-R', seed])
            original = base / 'raw-extraction'
            call(args.garbro, ['x', '-q', '-s', '-o', original, archive])
            baseline = base / 'original.json'
            workflow('init', '--original-root', original, '--archive', archive, '--format', tag, '--manifest', baseline)
            assert len(read(baseline)['entries']) == 4
            mapping = base / 'mapping.json'
            mapping.write_text(json.dumps([
                dict(chinese_text='这是第一句。', audio_files=['001.wav'], audio_paths=['Voice/char_a/001.wav'],
                     dialogue_id='open:1'),
                dict(chinese_text='这是第一句。这是第二句。', audio_files=['001.wav', '001.wav'],
                     audio_paths=['Voice/char_a/001.wav', 'Voice/char_b/001.wav'], dialogue_id='open:2',
                     audio_segments=[dict(chinese_text='这是第一句。'), dict(chinese_text='这是第二句。')])
            ], ensure_ascii=False), encoding='utf-8')
            adapter = base / 'fake_backend.py'
            adapter.write_text('''import wave,struct,math
class Backend:
    def synthesize(self, *, output_wav, text, **kwargs):
        assert text in {'这是第一句。', '这是第二句。'}, 'Do not synthesize the whole multi-segment line'
        with wave.open(output_wav,'wb') as output:
            output.setparams((1,2,16000,0,'NONE','not compressed'))
            output.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(i*0.2))) for i in range(3200)))
def create_backend(settings): return Backend()
''', encoding='utf-8')
            state = base / 'memory.json'
            output = base / 'generated'

            def tts(*arguments, success=True):
                return call(sys.executable, [TTS, '--memory', state, '--project', 'test', *arguments], success)

            tts('profile', 'test', '--adapter', adapter, '--python', sys.executable, '--ffmpeg', args.ffmpeg)
            tts('configure', '--input-json', mapping, '--asset-root', original, '--output-dir', output, '--profile', 'test')
            assert read(state)['projects']['test']['output_layout'] == 'relative'
            tts('plan')
            tts('run', '--limit', '1')
            handoff = output / '.galtts/resources.json'
            assert read(handoff)['complete'] is False
            workflow('merge', '--manifest', baseline, '--replacements', handoff,
                     '--staging', base / 'not-created', '--output', base / 'not-created.json', success=False)
            assert not (base / 'not-created').exists()
            tts('run')
            tts('handoff')
            assert read(handoff)['complete'] is True
            assert {entry['path'] for entry in read(handoff)['entries']} == {'Voice/char_a/001.wav', 'Voice/char_b/001.wav'}
            references = {entry['path']: entry['references'] for entry in read(handoff)['entries']}
            assert len(references['Voice/char_a/001.wav']) == 2
            assert len(references['Voice/char_b/001.wav']) == 1
            for character in ['char_a', 'char_b']:
                relative = Path('Voice') / character / '001.wav'
                assert (output / relative).is_file()
                assert sha(output / relative) != sha(original / relative)
            # Flat mode remains available for older jobs, and rejects ambiguous basenames.
            project = read(state)
            project['projects']['test']['output_layout'] = 'flat'
            state.write_text(json.dumps(project), encoding='utf-8')
            tts('plan', success=False)
            project['projects']['test']['output_layout'] = 'relative'
            state.write_text(json.dumps(project), encoding='utf-8')
            staged = base / 'staged.json'
            staging = base / 'staging'
            workflow('merge', '--manifest', baseline, '--replacements', handoff, '--staging', staging, '--output', staged)
            assert len(read(staged)['entries']) == 4
            assert (staging / 'scripts/start.tjs').read_bytes() == (original / 'scripts/start.tjs').read_bytes()
            assert not (staging / '.galtts').exists()
            rebuilt = base / ('rebuilt.' + tag.lower())
            report = base / 'verified.json'
            workflow('pack', '--manifest', staged, '--garbro', args.garbro, '--output', rebuilt,
                     '--verification-dir', base / 'verified-files', '--report', report)
            result = read(report)
            assert result['passed'] and result['total'] == 4 and result['retained'] == 2 and result['replaced'] == 2
            # Independent verify detects corruption rather than trusting a successful creation exit code.
            bad_manifest = read(staged)
            bad_manifest['entries'][0]['expected_sha256'] = '0' * 64
            changed_manifest = base / 'wrong-hash.json'
            changed_manifest.write_text(json.dumps(bad_manifest), encoding='utf-8')
            failed_report = base / 'failed-verification.json'
            workflow('verify', '--manifest', changed_manifest, '--garbro', args.garbro, '--archive', rebuilt,
                     '--verification-dir', base / 'failed-check', '--report', failed_report, success=False)
            assert read(failed_report)['passed'] is False
            # A changed staged file prevents creation of any output archive.
            (staging / 'scripts/start.tjs').write_bytes(b'tampered')
            rejected = base / 'rejected.arc'
            workflow('pack', '--manifest', staged, '--garbro', args.garbro, '--output', rejected,
                     '--verification-dir', base / 'unused-check', '--report', base / 'unused-report.json', success=False)
            assert not rejected.exists()
            # Patch mode includes only selected replacements, keeping the same internal paths.
            patch_manifest = base / 'patch.json'
            workflow('merge', '--manifest', baseline, '--replacements', handoff, '--staging', base / 'patch-staging',
                     '--output', patch_manifest, '--mode', 'patch')
            assert len(read(patch_manifest)['entries']) == 2
            workflow('pack', '--manifest', patch_manifest, '--garbro', args.garbro, '--output', base / 'patch.arc',
                     '--verification-dir', base / 'patch-check', '--report', base / 'patch-report.json')
            assert read(base / 'patch-report.json')['passed']
            # Changed replacement bytes, source bytes, mapping, and unsafe paths are rejected before merging.
            for case in ['replacement', 'source', 'mapping', 'traversal']:
                affected = output / 'Voice/char_a/001.wav' if case == 'replacement' else original / 'Voice/char_a/001.wav' if case == 'source' else mapping if case == 'mapping' else handoff
                saved = affected.read_bytes()
                if case == 'traversal':
                    data = read(handoff)
                    data['entries'][0]['path'] = '../outside.wav'
                    affected.write_text(json.dumps(data), encoding='utf-8')
                else:
                    affected.write_bytes(saved + b'changed')
                workflow('merge', '--manifest', baseline, '--replacements', handoff,
                         '--staging', base / ('rejected-' + case), '--output', base / (case + '.json'), success=False)
                assert not (base / ('rejected-' + case)).exists()
                affected.write_bytes(saved)
            # Existing artifacts are protected.
            workflow('init', '--original-root', original, '--archive', archive, '--format', tag, '--manifest', baseline, success=False)
            # Auditing a corrupted nested output invalidates the handoff, then restoration can be re-audited.
            audio = output / 'Voice/char_a/001.wav'
            saved = audio.read_bytes()
            audio.write_bytes(saved + b'changed')
            tts('handoff', success=False)
            assert read(handoff)['complete'] is False
            audio.write_bytes(saved)
            tts('handoff')
            assert read(handoff)['complete'] is True
            # A legacy flat output still carries its original archive path for reconstruction.
            legacy_mapping = base / 'legacy-mapping.json'
            legacy_mapping.write_text(json.dumps(read(mapping)[:1], ensure_ascii=False), encoding='utf-8')
            legacy_output = base / 'legacy-flat'
            tts('configure', '--input-json', legacy_mapping, '--output-dir', legacy_output, '--output-layout', 'flat')
            tts('run')
            assert (legacy_output / '001.wav').is_file()
            legacy_stage = base / 'legacy-staging'
            workflow('merge', '--manifest', baseline, '--replacements', legacy_output / '.galtts/resources.json',
                     '--staging', legacy_stage, '--output', base / 'legacy-staged.json')
            assert sha(legacy_stage / 'Voice/char_a/001.wav') == sha(legacy_output / '001.wav')
            assert sha(legacy_stage / 'Voice/char_b/001.wav') == sha(original / 'Voice/char_b/001.wav')
            checks.append(tag)
    print(json.dumps(dict(passed=True, formats=checks, used_real_model=False,
        checks=['nested duplicate basenames', 'shared voice references and explicit segments',
                'sample cannot be packed as full batch', 'source and replacement checksums',
                'retained resources', 'full and patch archive round trips', 'tamper rejection', 'safe paths',
                'existing artifact protection', 'audit invalidates stale handoff',
                'legacy flat output directory reconstruction']), indent=2))


if __name__ == '__main__':
    main()
