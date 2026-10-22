"""Bridge a model-specific CLI/service client through JSON request files."""
import json
from pathlib import Path
import subprocess
import sys


class CommandBackend:
    def __init__(self, settings):
        self.settings = settings
        if not isinstance(settings.get('argv'), list) or not settings['argv']:
            raise ValueError('command adapter requires a nonempty argv list; shell strings are unsupported')

    def synthesize(self, *, text, reference_audio, output_wav, language, seed, options):
        request_path = Path(output_wav).with_suffix('.request.json')
        request = dict(text=text, reference_audio=reference_audio, output_wav=output_wav,
                       language=language, seed=seed, options=options)
        request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding='utf-8')
        substitutions = {'{request_json}': str(request_path), '{output_wav}': output_wav,
                         '{reference_audio}': reference_audio}
        # Exact argv tokens only: no shell interpretation or text interpolation.
        argv = [substitutions.get(token, token) for token in self.settings['argv']]
        subprocess.run(argv, cwd=self.settings.get('cwd'), check=True,
                       stdout=sys.stdout, stderr=sys.stderr,
                       timeout=self.settings.get('timeout_seconds', 600))
        if not Path(output_wav).is_file():
            raise ValueError('The command succeeded without writing output_wav')


def create_backend(settings):
    return CommandBackend(settings)
