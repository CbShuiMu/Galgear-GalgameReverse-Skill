"""Exercise project persistence and stale-result checks without extracting any game."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile


def main():
    script = Path(__file__).with_name('memory.py')
    with tempfile.TemporaryDirectory(prefix='galextract-memory-') as temporary:
        root = Path(temporary)
        state = root / 'user-state/memory.json'
        game = root / 'game'
        game.mkdir()
        archive = game / 'data.arc'
        archive.write_bytes(b'archive-v1')
        output = root / 'export'
        output.mkdir()
        artifact = output / 'mapping.json'
        artifact.write_text('[]', encoding='utf-8')

        def cli(*argv, project='first', expected=0):
            command = [sys.executable, str(script), '--memory', str(state)]
            if project is not None:
                command += ['--project', project]
            result = subprocess.run([*command, *argv], text=True, encoding='utf-8',
                                    capture_output=True, env={**os.environ, 'PYTHONUTF8': '1'})
            assert result.returncode == expected, (argv, result.stdout, result.stderr)
            return result

        empty = json.loads(cli('memory', project=None).stdout)
        assert empty == dict(schema_version=1, last_project=None, projects={})
        assert not state.exists()
        assert Path(cli('memory', '--where', project=None).stdout.strip()) == state.resolve()
        cli('check', expected=1)
        cli('configure', '--game-root', str(game), '--output-dir', str(output))
        patch = root / 'findings.json'
        patch.write_text(json.dumps(dict(engine=dict(name='example-engine', confidence='tentative', evidence=['observed header']),
                                         tools=[dict(name='example-extractor', version='test-only', argv=['extractor', '--list'])],
                                         unresolved=['Confirm the archive version'])), encoding='utf-8')
        cli('update', '--patch', str(patch))
        patch.write_text(json.dumps(dict(engine=dict(confidence='confirmed'), counts=dict(audio=2), unresolved=[])), encoding='utf-8')
        cli('update', '--patch', str(patch))
        project = json.loads(cli('memory').stdout)
        assert project['engine']['name'] == 'example-engine'
        assert project['engine']['confidence'] == 'confirmed'
        assert project['engine']['evidence'] == ['observed header'] and not project['unresolved']
        new_output = root / 'new-export'
        cli('configure', '--output-dir', str(new_output))
        project = json.loads(cli('memory').stdout)
        assert project['output_dir'] == str(new_output.resolve()) and project['engine']['name'] == 'example-engine'

        cli('observe', '--source', str(archive), '--hash')
        cli('checkpoint', 'export_json', '--status', 'completed', '--artifact', str(artifact), '--hash')
        cli('check')
        before = state.read_bytes()
        cli('checkpoint', 'missing', '--status', 'completed', '--artifact', str(root / 'missing.json'), expected=1)
        assert state.read_bytes() == before
        outside = root / 'outside.arc'
        outside.write_bytes(b'outside')
        cli('observe', '--source', str(outside), expected=1)
        assert state.read_bytes() == before
        patch.write_text(json.dumps(dict(game_root=str(root))), encoding='utf-8')
        cli('update', '--patch', str(patch), expected=1)
        assert state.read_bytes() == before

        stat = artifact.stat()
        artifact.write_text('{}', encoding='utf-8')
        os.utime(artifact, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        changed = json.loads(cli('check', expected=1).stdout)
        assert any(issue['scope'] == 'artifact' and 'sha256' in issue['fields'] for issue in changed['issues'])
        artifact.write_text('[]', encoding='utf-8')
        os.utime(artifact, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        cli('check')
        source_stat = archive.stat()
        archive.write_bytes(b'archive-v2')
        os.utime(archive, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
        changed = json.loads(cli('check', expected=1).stdout)
        assert any(issue['scope'] == 'source' and 'sha256' in issue['fields'] for issue in changed['issues'])
        archive.write_bytes(b'archive-v1')
        os.utime(archive, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
        cli('check')
        artifact.unlink()
        missing = json.loads(cli('check', expected=1).stdout)
        assert any(issue['scope'] == 'artifact' and issue['reason'] == 'missing' for issue in missing['issues'])
        cli('checkpoint', 'extract_voice', '--status', 'stopped', '--notes', 'User requested a stop')
        assert json.loads(cli('memory').stdout)['checkpoints']['extract_voice']['status'] == 'stopped'

        other_game = root / 'other-game'
        other_game.mkdir()
        before = state.read_bytes()
        cli('configure', '--game-root', str(other_game), expected=1)
        assert state.read_bytes() == before
        cli('configure', '--game-root', str(other_game), '--output-dir', str(root / 'other-export'), project='second')
        assert 'engine' not in json.loads(cli('memory', project='second').stdout)
        assert json.loads(cli('memory', project='first').stdout)['engine']['name'] == 'example-engine'
        isolated = root / 'another-user'
        result = subprocess.run([sys.executable, str(script), 'memory'], check=True, text=True,
                                encoding='utf-8', capture_output=True,
                                env={**os.environ, 'GAL_EXTRACT_HOME': str(isolated), 'PYTHONUTF8': '1'})
        assert json.loads(result.stdout)['projects'] == {} and not isolated.exists()
        print(json.dumps(dict(passed=True, used_real_games=False,
                              checks=['empty first use', 'per-user isolation', 'configuration persistence',
                                      'findings merge and issue clearing', 'stage checkpoints',
                                      'source and artifact checksum changes', 'missing artifacts',
                                      'project isolation', 'unsafe patch and source rejection',
                                      'stopped status preserved without execution']), indent=2))


if __name__ == '__main__':
    main()
