"""Check resource identity and byte evidence on synthetic files, no game required."""
from pathlib import Path
import copy
import hashlib
import tempfile
import unittest

from validate_mapping import validate


class EvidenceTests(unittest.TestCase):
    def test_sources_spans_and_shared_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets = root/'assets'
            (assets/'voice').mkdir(parents=True)
            (assets/'voice/001.wav').write_bytes(b'original voice bytes')
            source = root/'source'
            source.mkdir()
            raw = b'MESSAGE|VOICE|NAME'
            (source/'open.bin').write_bytes(raw)
            row = dict(chinese_text='你好。', audio_files=['001.wav'], audio_paths=['voice/001.wav'], speaker='甲')
            rows = [row, dict(row)]
            evidence = dict(kind='gal-dialogue-evidence', schema_version=1,
                files=dict(script=dict(path='open.bin', sha256=hashlib.sha256(raw).hexdigest())),
                entries=[dict(row=i, relation='Synthetic message and voice parameters', spans=[
                    dict(role=role, file='script', offset=start, length=size,
                         sha256=hashlib.sha256(raw[start:start+size]).hexdigest())
                    for role, start, size in [('message', 0, 7), ('voice', 8, 5), ('speaker', 14, 4)]])
                    for i in range(2)])
            result = validate(rows, assets, evidence, source)
            self.assertEqual((result['rows'], result['voice_references'], result['unique_resources']), (2, 2, 1))
            self.assertTrue(result['tts_ready'])
            self.assertEqual(result['evidence']['semantics'], 'not_automatically_verified')
            changed = copy.deepcopy(evidence)
            changed['entries'][0]['spans'][0]['offset'] = 999
            with self.assertRaisesRegex(ValueError, 'outside'):
                validate(rows, assets, changed, source)
            changed = copy.deepcopy(evidence)
            changed['entries'][0]['spans'][0]['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                validate(rows, assets, changed, source)
            changed = copy.deepcopy(evidence)
            changed['entries'].pop()
            with self.assertRaisesRegex(ValueError, 'every mapping row'):
                validate(rows, assets, changed, source)
            (source/'open.bin').write_bytes(raw+b'changed')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                validate(rows, assets, evidence, source)

    def test_unready_segments_conflicts_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ['a.wav', 'b.wav']:
                (root/name).write_bytes(b'audio')
            row = dict(chinese_text='整句。', audio_files=['a.wav', 'b.wav'], audio_paths=['a.wav', 'b.wav'])
            self.assertFalse(validate([row], root)['tts_ready'])
            row['audio_segments'] = [dict(chinese_text='第一段。'), dict(chinese_text='第二段。')]
            self.assertTrue(validate([row], root)['tts_ready'])
            conflict = dict(chinese_text='冲突。', audio_files=['a.wav'], audio_paths=['a.wav'])
            self.assertFalse(validate([row, conflict], root)['tts_ready'])
            for path in ['../a.wav', '/a.wav', 'C:/a.wav', 'voice/../../a.wav']:
                with self.assertRaises((ValueError, FileNotFoundError)):
                    validate([dict(conflict, audio_paths=[path])], root)


if __name__ == '__main__':
    unittest.main()
