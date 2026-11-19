#!/usr/bin/env python3
"""Download five public pinned tokenizer and processor files via curl; excludes model weights."""
import json
import subprocess
from pathlib import Path
import convert_dataset as c
from verify_token_masks import TOKENIZER_MODEL, TOKENIZER_REVISION

snapshot = c.HERE / 'tokenizer'
manifest = json.loads((snapshot / 'snapshot_manifest.json').read_text())
c.require(manifest['repository'] == TOKENIZER_MODEL and manifest['revision'] == TOKENIZER_REVISION,
          'Unreviewed tokenizer identity')
c.require(set(manifest['artifacts']) == {'tokenizer.json', 'tokenizer_config.json', 'config.json', 'chat_template.jinja', 'processor_config.json'},
          'Only tokenizer/template artifacts may be downloaded')
for name, digest in manifest['artifacts'].items():
    target = snapshot / name
    if target.is_file() and c.sha_file(target) == digest:
        print(f'Verified cached {name}')
        continue
    temporary = target.with_name(name + '.download')
    try:
        subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '180',
                        f'https://huggingface.co/{TOKENIZER_MODEL}/resolve/{TOKENIZER_REVISION}/{name}',
                        '-o', str(temporary)], check=True)
        c.require(c.sha_file(temporary) == digest, f'Pinned tokenizer digest mismatch: {name}')
        temporary.replace(target)
        print(f'Downloaded and verified {name}')
    finally:
        temporary.unlink(missing_ok=True)
