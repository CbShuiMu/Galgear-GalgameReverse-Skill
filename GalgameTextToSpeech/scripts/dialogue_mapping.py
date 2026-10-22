"""Normalize dialogue occurrences before creating one task per audio resource.

Standard library only; this module neither opens audio nor loads a backend.
"""
import re


def clean_text(text):
    if not isinstance(text, str):
        raise ValueError('chinese_text must be a string; translation is a separate step')
    text = re.sub(r'\\+[nr]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_mapping(value):
    """Return one occurrence per voice reference, preserving dialogue identity.

    Resource resolution and deduplication belong to the caller: a filename alone
    cannot identify a resource, and flat output collisions are not shared audio.
    """
    if isinstance(value, dict):
        if value.get('kind', 'gal-dialogue-map') != 'gal-dialogue-map':
            raise ValueError('Expected a gal-dialogue-map, not a resource manifest')
        if value.get('schema_version', 1) != 1:
            raise ValueError('Unsupported dialogue mapping schema_version')
        value = value.get('entries')
    if not isinstance(value, list) or not value:
        raise ValueError('JSON must be a nonempty list, or an object with an entries list')
    occurrences, ids = [], set()
    for row_index, row in enumerate(value):
        label = f'Row {row_index}'
        if not isinstance(row, dict) or 'chinese_text' not in row:
            raise ValueError(f'{label}: missing chinese_text; translation is a separate step')
        whole_text = clean_text(row['chinese_text'])
        explicit_id = row.get('dialogue_id')
        if explicit_id is not None:
            if not isinstance(explicit_id, str) or not explicit_id.strip() or explicit_id in ids:
                raise ValueError(f'{label}: dialogue_id must be a unique nonempty string')
            ids.add(explicit_id)
        speaker = row.get('speaker')
        if speaker is not None and not isinstance(speaker, str):
            raise ValueError(f'{label}: speaker must be a string or null')
        source = row.get('source')
        if source is not None and not isinstance(source, dict):
            raise ValueError(f'{label}: source must be an object')
        names, paths = row.get('audio_files'), row.get('audio_paths')
        if not isinstance(names, list) or not names or any(not isinstance(n, str) or not n for n in names):
            raise ValueError(f'{label}: audio_files must be a nonempty list of filenames')
        if paths is not None and (not isinstance(paths, list) or len(paths) != len(names)
                                  or any(not isinstance(p, str) or not p for p in paths)):
            raise ValueError(f'{label}: audio_files/audio_paths must align')
        segments = row.get('audio_segments')
        if len(names) > 1 and segments is None:
            raise ValueError(f'{label}: multiple audio files require explicit audio_segments; do not repeat the whole line')
        if segments is not None and (not isinstance(segments, list) or len(segments) != len(names)):
            raise ValueError(f'{label}: audio_segments must align with audio_files')
        for voice_index, name in enumerate(names):
            text = whole_text
            if segments is not None:
                segment = segments[voice_index]
                if not isinstance(segment, dict) or 'chinese_text' not in segment:
                    raise ValueError(f'{label}: each audio_segments item needs chinese_text')
                text = clean_text(segment['chinese_text'])
            reference = dict(row=row_index, voice_index=voice_index,
                             dialogue_id=explicit_id, speaker=speaker)
            if source is not None:
                reference['source'] = source
            occurrences.append(dict(name=name, path=None if paths is None else paths[voice_index],
                                    text=text, reference=reference))
    return occurrences
