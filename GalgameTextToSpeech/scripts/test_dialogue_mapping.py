"""Test reference-to-resource planning without audio libraries or a TTS backend."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import copy
import json
import tempfile
import unittest

from dialogue_mapping import normalize_mapping
from galtts import build_plan


def row(text='你好。', path='voice/001.wav', **fields):
    return dict(chinese_text=text, audio_files=[path.rsplit('/', 1)[-1]], audio_paths=[path], **fields)


class MappingTests(unittest.TestCase):
    def test_legacy_and_versioned_inputs(self):
        expected = normalize_mapping([row()])
        self.assertEqual(expected, normalize_mapping(dict(entries=[row()])))
        self.assertEqual(expected, normalize_mapping(dict(kind='gal-dialogue-map', schema_version=1, entries=[row()])))
        for value in [dict(kind='gal-resource-manifest', entries=[row()]), dict(schema_version=2, entries=[row()])]:
            with self.assertRaises(ValueError):
                normalize_mapping(value)

    def test_explicit_segments_and_identity(self):
        item = dict(chinese_text='你好。出发吧。', audio_files=['001.wav', '002.wav'],
                    audio_paths=['voice/001.wav', 'voice/002.wav'], dialogue_id='open:12',
                    speaker='角色甲', source=dict(script='open.bin', offset=42),
                    audio_segments=[dict(chinese_text='你好。'), dict(chinese_text='出发吧。')])
        found = normalize_mapping([item])
        self.assertEqual([f['text'] for f in found], ['你好。', '出发吧。'])
        self.assertEqual(found[1]['reference']['voice_index'], 1)
        self.assertEqual(found[1]['reference']['source'], item['source'])
        missing = dict(item)
        missing.pop('audio_segments')
        with self.assertRaisesRegex(ValueError, 'audio_segments'):
            normalize_mapping([missing])
        with self.assertRaisesRegex(ValueError, 'dialogue_id'):
            normalize_mapping([item, item])

    def test_invalid_segments_and_metadata(self):
        for item in [dict(row(), audio_segments=[]), dict(row(), audio_segments=[{}]),
                     dict(row(), audio_segments=[dict(chinese_text=3)]),
                     row(speaker=42), row(source='guess'), row(dialogue_id='')]:
            with self.assertRaises(ValueError):
                normalize_mapping([item])

    def test_resource_grouping_conflict_and_flat_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets = root / 'assets'
            for path in ['voice/001.wav', 'other/001.wav', 'voice/002.wav']:
                file = assets / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b'synthetic resource')
            mapping = root / 'mapping.json'
            adapter = root / 'adapter.py'
            adapter.write_text('raise AssertionError("backend must not load")', encoding='utf-8')
            ffmpeg = root / 'not-executed.exe'
            ffmpeg.write_bytes(b'not executed')
            profile = dict(adapter=str(adapter), ffmpeg=str(ffmpeg))
            project = dict(input_json=str(mapping), asset_root=str(assets), output_dir=str(root/'out'),
                           output_layout='relative', profile='test')
            fake_audio = SimpleNamespace(EXTENSIONS={'.wav'}, export_args=lambda *args: None,
                                         probe=lambda path: SimpleNamespace(to_dict=lambda: dict(codec='fake')))

            def plan(rows):
                mapping.write_text(json.dumps(rows), encoding='utf-8')
                with patch.dict('sys.modules', audio_formats=fake_audio):
                    return build_plan(project, profile)

            first = row(dialogue_id='open:1', speaker='甲')
            second = row(dialogue_id='open:2', speaker='甲')
            untouched = copy.deepcopy([first, second])
            single = plan([first])
            shared = plan([first, second])
            self.assertEqual((shared['total'], shared['total_references'], shared['reused_references']), (1, 2, 1))
            self.assertEqual(len(shared['tasks'][0]['references']), 2)
            self.assertEqual(single['tasks'][0]['fingerprint'], shared['tasks'][0]['fingerprint'])
            self.assertEqual([first, second], untouched)
            with self.assertRaisesRegex(ValueError, 'Conflicting text'):
                plan([first, row('另一句话。')])
            self.assertEqual(plan([first, row(path='other/001.wav')])['total'], 2)
            project['output_layout'] = 'flat'
            with self.assertRaisesRegex(ValueError, 'Duplicate output path'):
                plan([first, row(path='other/001.wav')])
            project['output_layout'] = 'relative'
            split = dict(chinese_text='整句。', audio_files=['001.wav', '002.wav'],
                         audio_paths=['voice/001.wav', 'voice/002.wav'],
                         audio_segments=[dict(chinese_text='第一段。'), dict(chinese_text='第二段。')])
            self.assertEqual([t['text'] for t in plan([split])['tasks']], ['第一段。', '第二段。'])
            self.assertFalse((root/'out').exists())


if __name__ == '__main__':
    unittest.main()
