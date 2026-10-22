"""Probe real audio formats and export synthesized PCM with matching properties."""
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import re
import subprocess


EXTENSIONS = {'.wav', '.wave', '.flac', '.ogg', '.oga', '.opus', '.mp3', '.mp2',
              '.m4a', '.aac', '.aif', '.aiff', '.aifc', '.wma', '.caf', '.au', '.snd',
              '.webm', '.ac3', '.ape', '.amr'}


@dataclass(frozen=True)
class AudioSpec:
    container: str
    codec: str
    samplerate: int
    channels: int
    seconds: float
    bits: int = 0
    bitrate: int = 0

    def to_dict(self):
        return asdict(self)


def probe(path):
    import av
    with av.open(str(path)) as media:
        streams = list(media.streams.audio)
        if len(streams) != 1:
            raise ValueError(f'Expected exactly one audio stream: {path}')
        stream = streams[0]
        ctx = stream.codec_context
        codec = ctx.codec.canonical_name
        container = media.format.name
        seconds = (float(stream.duration * stream.time_base) if stream.duration is not None
                   else float(media.duration / av.time_base) if media.duration else 0.0)
        bits_match = re.match(r'pcm_[suf](\d+)', codec)
        bits = int(bits_match[1]) if bits_match else 0
        if codec in {'flac', 'alac'}:
            # libsndfile exposes FLAC's valid bit depth; ALAC can be obtained from frames.
            try:
                import soundfile as sf
                subtype = sf.info(path).subtype
                bits = int(subtype.split('_')[-1]) if subtype.startswith('PCM_') else 0
            except (RuntimeError, ValueError):
                pass
            if not bits:
                frame = next(media.decode(stream), None)
                if frame is not None:
                    bits = frame.format.bits
        spec = AudioSpec(container, codec, ctx.sample_rate, ctx.channels, seconds,
                         bits, ctx.bit_rate or 0)
        if spec.samplerate <= 0 or spec.channels <= 0:
            raise ValueError(f'Missing sample rate or channel count: {path}')
        return spec


def ffmpeg_run(ffmpeg, args):
    result = subprocess.run([str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-nostdin', *args],
                            capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


@lru_cache(maxsize=4)
def encoders(ffmpeg):
    listing = subprocess.run([str(ffmpeg), '-hide_banner', '-encoders'], check=True,
                             capture_output=True, text=True, encoding='utf-8').stdout
    return set(re.findall(r'^\s*A\S{5}\s+(\S+)', listing, re.MULTILINE))


def export_args(spec, suffix, ffmpeg, vorbis_quality=5):
    """Reject unsupported codec/container pairs instead of changing them silently."""
    suffix = suffix.lower()
    formats = set(spec.container.split(','))
    muxer = None
    if suffix in {'.wav', '.wave'} and 'wav' in formats:
        muxer = 'wav'
    elif suffix == '.flac' and 'flac' in formats:
        muxer = 'flac'
    elif suffix in {'.ogg', '.oga', '.opus'} and 'ogg' in formats:
        muxer = 'ogg'
    elif suffix in {'.mp3', '.mp2'} and formats & {'mp3', 'mp2'}:
        muxer = 'mp3' if spec.codec == 'mp3' else 'mp2'
    elif suffix == '.m4a' and formats & {'mov', 'mp4', 'm4a'}:
        muxer = 'ipod'
    elif suffix == '.aac' and 'aac' in formats:
        muxer = 'adts'
    elif suffix in {'.aif', '.aiff', '.aifc'} and 'aiff' in formats:
        muxer = 'aiff'
    elif suffix == '.wma' and 'asf' in formats:
        muxer = 'asf'
    elif suffix == '.caf' and 'caf' in formats:
        muxer = 'caf'
    elif suffix in {'.au', '.snd'} and 'au' in formats:
        muxer = 'au'
    elif suffix == '.webm' and formats & {'webm', 'matroska'}:
        muxer = 'webm'
    elif suffix == '.ac3' and 'ac3' in formats:
        muxer = 'ac3'
    if muxer is None:
        raise ValueError(f'Unsupported or mismatched container: {suffix}, {spec.container}, {spec.codec}')

    allowed = {
        'wav': {'pcm_u8', 'pcm_s16le', 'pcm_s24le', 'pcm_s32le', 'pcm_f32le', 'pcm_f64le',
                'pcm_alaw', 'pcm_mulaw', 'adpcm_ima_wav', 'adpcm_ms'},
        'aiff': {'pcm_s8', 'pcm_s16be', 'pcm_s24be', 'pcm_s32be', 'pcm_f32be', 'pcm_f64be'},
        'flac': {'flac'}, 'ogg': {'vorbis', 'opus', 'flac'}, 'mp3': {'mp3'}, 'mp2': {'mp2'},
        'ipod': {'aac', 'alac'}, 'adts': {'aac'}, 'asf': {'wmav1', 'wmav2'},
        'caf': {'pcm_s16le', 'pcm_s24le', 'pcm_s32le', 'pcm_f32le', 'alac'},
        'au': {'pcm_s8', 'pcm_s16be', 'pcm_s24be', 'pcm_s32be', 'pcm_mulaw', 'pcm_alaw'},
        'webm': {'opus', 'vorbis'}, 'ac3': {'ac3'},
    }
    codec = spec.codec
    if codec not in allowed[muxer]:
        raise ValueError(f'No matching export implementation: {muxer}/{codec}')
    encoder = {'vorbis': 'libvorbis', 'opus': 'libopus', 'mp3': 'libmp3lame'}.get(codec, codec)
    if encoder not in encoders(str(ffmpeg)):
        raise ValueError(f'FFmpeg encoder unavailable: {encoder}')
    args = ['-map', '0:a:0', '-vn', '-ar', str(spec.samplerate), '-ac', str(spec.channels),
            '-c:a', encoder, '-f', muxer]
    if codec == 'vorbis':
        args += ['-q:a', str(vorbis_quality)]
    elif codec == 'mp3':
        args += ['-q:a', '2']
    elif codec in {'aac', 'opus', 'wmav1', 'wmav2', 'mp2', 'ac3'}:
        args += ['-b:a', str(spec.bitrate or (128000 * min(spec.channels, 2)))]
    elif codec in {'flac', 'alac'}:
        if spec.bits not in {16, 24, 32}:
            raise ValueError(f'Cannot preserve {codec} bit depth: {spec.bits}')
        args += ['-sample_fmt', 's16' if spec.bits == 16 else 's32',
                 '-bits_per_raw_sample', str(spec.bits)]
    return args


def verify_match(expected, actual):
    fields = ('codec', 'samplerate', 'channels')
    if expected.container != actual.container:
        raise ValueError(f'Container differs: {expected.container} -> {actual.container}')
    for key in fields:
        if getattr(expected, key) != getattr(actual, key):
            raise ValueError(f'{key} differs: {getattr(expected,key)} -> {getattr(actual,key)}')
    if expected.bits and expected.bits != actual.bits:
        raise ValueError(f'Bit depth differs: {expected.bits} -> {actual.bits}')
    if actual.seconds <= 0:
        raise ValueError('Empty output audio')


def validate_signal(path, ffmpeg):
    import numpy as np
    raw = ffmpeg_run(ffmpeg, ['-i', str(path), '-map', '0:a:0', '-f', 'f32le', '-c:a', 'pcm_f32le', '-'])
    samples = np.frombuffer(raw, dtype='<f4')
    if not samples.size or not np.isfinite(samples).all():
        raise ValueError(f'Empty or non-finite audio: {path}')
    if float(np.abs(samples).max()) < 0.0001:
        raise ValueError(f'Silent generated audio: {path}')


def encode_like(wav, target, source_spec, ffmpeg, vorbis_quality=5):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.stem + '.partial' + target.suffix)
    options = export_args(source_spec, target.suffix, ffmpeg, vorbis_quality)
    try:
        ffmpeg_run(ffmpeg, ['-y', '-i', str(wav), *options, str(temporary)])
        result = probe(temporary)
        verify_match(source_spec, result)
        validate_signal(temporary, ffmpeg)
        temporary.replace(target)
        return result
    finally:
        temporary.unlink(missing_ok=True)


def reference_wav(source, target, ffmpeg):
    """Supply every backend with an ordinary PCM WAV, also for M4A/WMA sources."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_run(ffmpeg, ['-y', '-i', str(source), '-map', '0:a:0', '-vn',
                        '-c:a', 'pcm_f32le', str(target)])
    return target
