"""Exercise the experience lifecycle in isolated installed skill copies.

Reports simulate successful metadata; no real game success is claimed or added
to the repository, and the user's actual experience store is never opened.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGES = {'GalgameReverse': 'reverse', 'GalgameResourceExtract': 'extract', 'GalgameResourcePack': 'pack'}


class ExperienceTests(unittest.TestCase):
    def test_isolated_lifecycle_for_each_stage(self):
        for folder, stage in STAGES.items():
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix='gal-experience-test-') as temporary:
                root = Path(temporary)
                skill = root/'installed-skill'
                (skill/'scripts').mkdir(parents=True)
                (skill/'catalog').mkdir()
                (skill/'engine').mkdir()
                manual_page = skill/'engine/fixture-engine.md'
                manual_notes = '# Fixture engine\n\nExisting format notes must remain intact.\n'
                manual_page.write_text(manual_notes, encoding='utf-8')
                shutil.copyfile(ROOT/folder/'SKILL.md', skill/'SKILL.md')
                helper = skill/'scripts/engine_experience.py'
                shutil.copyfile(ROOT/folder/'scripts/engine_experience.py', helper)
                store = root/'user-store'

                def cli(*arguments, success=True):
                    result = subprocess.run([sys.executable, str(helper), '--store', str(store), *arguments],
                        capture_output=True, encoding='utf-8', timeout=30,
                        env={**os.environ, 'PYTHONUTF8': '1'})
                    self.assertEqual(result.returncode == 0, success, result.stdout+result.stderr)
                    return json.loads(result.stdout) if success else result.stderr

                self.assertEqual(cli('query')['entries'], [])
                self.assertFalse(store.exists())
                source = root/'source.bin'
                source.write_bytes(b'synthetic source fixture')
                result = root/'verification.json'
                result.write_text('{"fixture_check":"passed"}', encoding='utf-8')
                report = json.loads((ROOT/folder/'assets/engine-experience.example.json').read_text(encoding='utf-8'))
                report.update(engine='fixture-engine', engine_version='v1', variant='test layout',
                              summary='Test the metadata lifecycle, no real game claim',
                              preconditions=['Known fixed fixture layout'], steps=['Use the fixture validator'],
                              limitations=['Metadata simulation only'])
                for key, path in [('source', source), ('verification', result)]:
                    report['artifacts'][key].update(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                report_file = root/'success.json'

                def save():
                    report_file.write_text(json.dumps(report), encoding='utf-8')

                save()
                recorded = cli('record', '--report', str(report_file))
                identifier = recorded['id']
                self.assertEqual(cli('record', '--report', str(report_file))['id'], identifier)
                self.assertFalse(cli('query', '--engine', 'fixture-engine', '--version', 'v2')['entries'][0]['version_match'])
                promoted = cli('promote', '--id', identifier)
                page = Path(promoted['page']).read_text(encoding='utf-8')
                self.assertEqual(Path(promoted['page']), manual_page)
                self.assertTrue(page.startswith(manual_notes))
                self.assertNotIn(str(root), page)
                self.assertEqual(len(json.loads(Path(promoted['index']).read_text())['entries']), 1)
                cli('promote', '--id', identifier)
                self.assertEqual(manual_page.read_text(encoding='utf-8'), page)
                first_report = json.loads(json.dumps(report))
                report['summary'] = 'Another verified condition for the same engine'
                save()
                another = cli('record', '--report', str(report_file))['id']
                second = cli('promote', '--id', another)
                self.assertEqual(second['page'], promoted['page'])
                combined = manual_page.read_text(encoding='utf-8')
                self.assertTrue(combined.startswith(page.rstrip('\n')))
                self.assertIn(identifier, combined)
                self.assertIn(another, combined)
                self.assertEqual(len(json.loads(Path(promoted['index']).read_text())['entries']), 2)
                corrected = combined.replace(first_report['summary'], 'A manually corrected lesson', 1)
                manual_page.write_text(corrected, encoding='utf-8')
                cli('promote', '--id', identifier, success=False)
                self.assertEqual(manual_page.read_text(encoding='utf-8'), corrected)
                manual_page.write_text(combined, encoding='utf-8')
                report = first_report
                save()
                result.write_text('changed evidence', encoding='utf-8')
                self.assertIn('changed', cli('promote', '--id', identifier, success=False))
                result.write_text('{"fixture_check":"passed"}', encoding='utf-8')
                cli('invalidate', '--id', identifier, '--reason', 'New evidence contradicts the assumption')
                self.assertEqual([entry['id'] for entry in cli('query')['entries']], [another])
                self.assertEqual(cli('query')['invalidated'][0]['id'], identifier)
                self.assertEqual(json.loads(Path(promoted['index']).read_text())['entries'][0]['status'], 'invalidated')
                cli('promote', '--id', identifier, success=False)
                self.assertEqual(cli('record', '--report', str(report_file))['status'], 'invalidated')
                report['validation_level'] = 'synthetic'
                save()
                synthetic = cli('record', '--report', str(report_file))['id']
                self.assertIn('Synthetic', cli('promote', '--id', synthetic, success=False))
                report['validation_level'] = 'real_sample'
                report['preconditions'] = ['C:/Games/private-project']
                save()
                private = cli('record', '--report', str(report_file))['id']
                self.assertIn('local path', cli('promote', '--id', private, success=False))
                report['checks'][0]['status'] = 'failed'
                save()
                cli('record', '--report', str(report_file), success=False)


if __name__ == '__main__':
    unittest.main()
