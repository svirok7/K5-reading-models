"""Build the minimal upload archive deterministically and update notebook hash pins."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent

def digest(value):
    return hashlib.sha256(value).hexdigest()


def build():
    inputs = {
        'sft_train.py': ROOT / 'sft_train.py',
        'requirements-sft-colab.txt': ROOT / 'requirements-sft-colab.txt',
        'data/sft.jsonl': ROOT / 'datasets/sft-300-v2/sft.jsonl',
        'data/manifest.json': ROOT / 'datasets/sft-300-v2/manifest.json',
    }
    payload = {name: path.read_bytes() for name, path in inputs.items()}
    manifest = {
        'dataset': 'sft-300-v2',
        'default_training_mode': 'lora',
        'supported_training_modes': ['lora', 'qlora'],
        'files': {name: digest(data) for name, data in payload.items()},
    }
    payload['kit-manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    archive = ROOT / 'reading-sft-colab-v2.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as kit:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            kit.writestr(info, data)
    kit_hash = digest(archive.read_bytes())
    (ROOT / 'reading-sft-colab-v2.sha256').write_text(f'{kit_hash}  {archive.name}\n')
    notebook_path = ROOT / 'sft_colab.ipynb'
    notebook = json.loads(notebook_path.read_text())
    replacements = 0
    for cell in notebook['cells']:
        source = ''.join(cell['source'])
        source, count = re.subn(r"EXPECTED_KIT_SHA256\s*=\s*'[a-f0-9]{64}'",
                               f"EXPECTED_KIT_SHA256 = '{kit_hash}'", source)
        replacements += count
        cell['source'] = source.splitlines(keepends=True)
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None
    if replacements != 1:
        raise ValueError(f'Expected exactly one notebook kit pin; found {replacements}')
    notebook_path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + '\n')
    with zipfile.ZipFile(archive) as kit:
        assert kit.testzip() is None
        assert set(kit.namelist()) == set(payload)
        for name, expected in manifest['files'].items():
            assert digest(kit.read(name)) == expected
    report = {'upload_kit_bytes': archive.stat().st_size,
              'upload_kit_sha256': kit_hash, 'upload_kit_files': sorted(payload),
              'notebook_sha256': digest(notebook_path.read_bytes())}
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    build()
