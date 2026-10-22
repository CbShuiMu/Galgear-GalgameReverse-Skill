"""Check runtime entrypoints after relocation without repository siblings."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StandaloneTests(unittest.TestCase):
    def test_relocated_entrypoints_and_mapping(self):
        for name in ['GalgameResourceExtract', 'GalgameTextToSpeech', 'GalgameResourcePack', 'GalgameReverse']:
            with self.subTest(skill=name), tempfile.TemporaryDirectory(prefix='gal-standalone-') as temporary:
                root = Path(temporary)
                skill = root/'installed'
                scripts = skill/'scripts'
                scripts.mkdir(parents=True)
                shutil.copyfile(ROOT/name/'SKILL.md', skill/'SKILL.md')
                for file in (ROOT/name/'scripts').glob('*.py'):
                    if not file.name.startswith('test_'):
                        shutil.copyfile(file, scripts/file.name)

                def call(*arguments):
                    result = subprocess.run([sys.executable, *map(str, arguments)], cwd=skill,
                        capture_output=True, encoding='utf-8', timeout=30,
                        env={**os.environ, 'PYTHONUTF8': '1'})
                    self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                    return result.stdout

                if name == 'GalgameResourceExtract':
                    state = root/'new-state.json'
                    empty = json.loads(call(scripts/'memory.py', '--memory', state, 'memory'))
                    self.assertEqual(empty['projects'], {})
                    assets = root/'assets'
                    assets.mkdir()
                    (assets/'a.wav').write_bytes(b'fixture bytes, no decoder required')
                    mapping = root/'mapping.json'
                    mapping.write_text(json.dumps([dict(chinese_text='你好。', audio_files=['a.wav'], audio_paths=['a.wav'])]))
                    result = json.loads(call(scripts/'validate_mapping.py', '--mapping', mapping, '--asset-root', assets))
                    self.assertTrue(result['tts_ready'])
                    self.assertFalse(state.exists())
                elif name == 'GalgameTextToSpeech':
                    state = root/'new-state.json'
                    result = json.loads(call(scripts/'galtts.py', '--memory', state, 'memory'))
                    self.assertEqual(result['profiles'], {})
                    self.assertFalse(state.exists())
                elif name == 'GalgameResourcePack':
                    self.assertIn('init', call(scripts/'resource_workflow.py', '--help'))
                else:
                    store = root/'store'
                    self.assertEqual(json.loads(call(scripts/'engine_experience.py', '--store', store, 'query'))['entries'], [])
                    self.assertFalse(store.exists())


if __name__ == '__main__':
    unittest.main()
