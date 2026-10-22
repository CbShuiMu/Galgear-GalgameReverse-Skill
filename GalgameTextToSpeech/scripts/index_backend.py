"""IndexTTS 2.0/2.5 adapter; one model instance for an entire batch."""
from pathlib import Path
import gc
import contextlib
import io
import os
import sys


class IndexBackend:
    def __init__(self, settings):
        project = Path(settings['project_dir']).resolve()
        if not (project / 'indextts').is_dir():
            raise FileNotFoundError(f'IndexTTS source checkout not found: {project}')
        self.previous_cwd = Path.cwd()
        self.version = str(settings.get('version', ''))
        if self.version not in {'2', '2.5'}:
            raise ValueError('Select an Index version explicitly: set version to 2 or 2.5')
        sys.path.insert(0, str(project))
        os.environ['USE_MODELSCOPE'] = 'false'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.chdir(project)
        import torch
        self.torch = torch
        if 'threads' in settings:
            torch.set_num_threads(settings['threads'])
        if self.version == '2.5':
            from indextts.infer_v2_5 import IndexTTS2
            precision = {'use_bf16': settings.get('half_precision', True)}
        else:
            from indextts.infer_v2 import IndexTTS2
            precision = {'use_fp16': settings.get('half_precision', True)}
        model_dir = Path(settings.get('model_dir', 'checkpoints' if self.version == '2.5' else 'checkpoints_2'))
        common = dict(cfg_path=str(model_dir / 'config.yaml'), model_dir=str(model_dir),
                      use_qwen_emo=False, use_cuda_kernel=False, use_deepspeed=False)
        if settings.get('cpu_encoder', False):
            # Some checkouts add this option; do not assume upstream supports it.
            import inspect
            if 'cpu_encoder' not in inspect.signature(IndexTTS2).parameters:
                raise ValueError('This IndexTTS checkout does not support cpu_encoder; patch it or change the profile')
            common['cpu_encoder'] = True
        self.tts = IndexTTS2(**common, **precision)

    def synthesize(self, *, text, reference_audio, output_wav, language, seed, options):
        self.torch.manual_seed(seed)
        options = dict(options)
        emotion_audio = options.pop('emotion_reference_audio', None)
        generation = dict(num_beams=1, do_sample=True, top_p=0.8, top_k=30,
                          temperature=0.8, repetition_penalty=10.0,
                          max_text_tokens_per_segment=60, max_mel_tokens=1500, verbose=False)
        generation.update(options)
        # A generic duration_factor can only be forwarded to versions that implement it.
        if self.version == '2':
            generation.pop('duration_factor', None)
        else:
            generation['lang'] = language.upper()
        capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                self.tts.infer(spk_audio_prompt=reference_audio, text=text, output_path=output_wav,
                               emo_audio_prompt=emotion_audio, **generation)
        finally:
            print(capture.getvalue())
        if 'exceeding `max_mel_tokens`' in capture.getvalue():
            raise ValueError('IndexTTS generation reached max_mel_tokens; output may be truncated')

    def close(self):
        del self.tts
        gc.collect()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
        os.chdir(self.previous_cwd)


def create_backend(settings):
    return IndexBackend(settings)
