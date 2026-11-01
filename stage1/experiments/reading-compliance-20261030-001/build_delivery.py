"""Seal a fresh executable package after independent data approval. Never overwrite."""
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys
import zipfile

HERE=Path(__file__).resolve().parent
STAGE=HERE.parents[1]
sys.path.insert(0,str(STAGE))
import sft_train as t


def cell(kind,source):
    result=dict(cell_type=kind,metadata={},source=source.splitlines(keepends=True))
    if kind=='code': result.update(execution_count=None,outputs=[])
    return result


def build(preparation_only=False):
    for name in ('plan.json','reading-compliance-colab.zip','reading_compliance_colab.ipynb','delivery.json'):
        if (HERE/name).exists():
            raise ValueError('Sealed artifact exists; never overwrite completed experiment: '+name)
    baseline=STAGE/'datasets/sft-300-v2'
    successor=STAGE/'datasets/sft-600-v1'
    config=None
    if not preparation_only:
        data=json.loads((successor/'manifest.json').read_text())
        config=t.TrainConfig(epochs=3,dataset_version=data['version'],data_sha256=t.sha256(successor/'sft.jsonl'),manifest_sha256=t.sha256(successor/'manifest.json'),train_examples=600)
        t.verify_data(successor,config)
    t.verify_data(baseline)
    frozen=HERE/'frozen'
    frozen_sha=t.sha256(frozen/'manifest.json')
    import evaluate
    evaluate.frozen(frozen,frozen_sha)
    historical=STAGE/'runs/qwen-sft300-v2-lora-allocator-20261030-008'
    shutil.copyfile(historical/'run-record.json',HERE/'current-adapter-record.json')
    # Hash verify the actual current adapter before recording it in the plan.
    evaluate.verify_adapter(historical/'adapter',HERE/'current-adapter-record.json',t.sha256(HERE/'current-adapter-record.json'))
    script_names=['evaluate.py','execute.py','choose_checkpoint.py','plot_results.py','repeat_seeds.py','validate_authoring.py','test_evaluate.py','test_selection.py','build_delivery.py']
    code_files={str((HERE/name).relative_to(STAGE)):t.sha256(HERE/name) for name in script_names}
    code_files.update({name:t.sha256(STAGE/name) for name in ('sft_train.py','test_sft_train.py','requirements-sft-colab.txt','sft_colab.ipynb')})
    packages={}
    for package in ('torch','transformers','peft','accelerate','tokenizers','huggingface_hub','safetensors'):
        try: packages[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: packages[package]=None
    plan=dict(schema_version=1,experiment_id=HERE.name,status='prepared_gpu_access_blocked',model=t.MODEL_ID,revision=t.REVISION,
        prompt_sha256=t.sha256(frozen/'prompt-B.txt'),frozen_manifest_sha256=frozen_sha,helper_sha256=t.sha256(STAGE/'sft_train.py'),code_files=code_files,
        current_adapter_record_sha256=t.sha256(HERE/'current-adapter-record.json'),current_adapter_artifacts=json.loads((historical/'run-record.json').read_text())['adapter_artifacts'],
        generation=evaluate.GENERATION,inference=dict(hardware='Tesla T4',precision='float16',template=evaluate.TEMPLATE,enable_thinking=False,seed_offsets=[0,1000003,2000003]),
        prepared_environment=dict(python=platform.python_version(),platform=platform.platform(),packages=packages),
        experiments=[dict(name='same300',dataset='datasets/sft-300-v2',config=asdict(t.TrainConfig(epochs=3)),optimizer_updates=114,row_exposures=900),dict(name='expanded600',dataset='datasets/sft-600-v1',config=asdict(config) if config else None,optimizer_updates=225,row_exposures=1800)],
        selection=dict(min_primary_joint_gain_pp=20,no_new_serious_safety_or_identity_failures=True,tie_break='earlier_epoch_then_fewer_updates',repeats_require='positive gain on both additional paired seed offsets; same cases',human_review_pending=True),
        limitations=['The epoch-one checkpoint of the fresh3-epoch run has a different LR trajectory from historical1-epoch training.','Expanded data also increases total updates114->225; this is not a pure data-size ablation.','Fixed histories measure next-turn responses, not autonomous conversations.','34 selected development cases; not held-out generalization evidence.'],
        prohibitions=dict(test_access=False,new_development_cases=False,paid_judge=False,compute_purchase=False,live_ui_change=False))
    if preparation_only:
        plan['status']='partial_preparation_gpu_and_independent_review_blocked'
        plan['pending_experiments']=[dict(name='expanded600',reason='600-example corpus is incomplete and not independently approved; no training configuration authorized')]
        plan['experiments']=[row for row in plan['experiments'] if row['name']=='same300']
        plan['selection']['adoption_blocked_until_both_experiments_complete']=True
    prepared=json.loads((HERE/'prepared-model-artifacts.json').read_text())
    if prepared['model'] != t.MODEL_ID or prepared['revision'] != t.REVISION or prepared['aggregate_sha256'] != evaluate.digest(prepared['files']):
        raise ValueError('Prepared model artifact record differs')
    plan['prepared_model_artifacts']=prepared['files']
    plan['prepared_model_artifacts_sha256']=prepared['aggregate_sha256']
    plan['prepared_environment_sha256']=evaluate.digest(plan['prepared_environment'])
    t.write_json(HERE/'plan.json',plan)
    files={}
    for relative in code_files:
        files['stage1/'+relative]=STAGE/relative
    for directory in ((baseline,) if preparation_only else (baseline,successor)):
        for name in ('sft.jsonl','manifest.json'):
            path=directory/name
            files['stage1/'+str(path.relative_to(STAGE))]=path
    for path in frozen.iterdir():
        if path.is_file(): files['stage1/'+str(path.relative_to(STAGE))]=path
    for name in ('plan.json','current-adapter-record.json','REVIEW_PROTOCOL.md','README.md','prepared-model-artifacts.json'):
        path=HERE/name
        files['stage1/'+str(path.relative_to(STAGE))]=path
    for name in ('RUBRIC.md','READER_PROFILE.txt'):
        files['stage1/'+name]=STAGE/name
    payload={name:path.read_bytes() for name,path in files.items()}
    kit_manifest=dict(plan_sha256=t.sha256(HERE/'plan.json'),files={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()})
    payload['kit-manifest.json']=(json.dumps(kit_manifest,indent=2)+'\n').encode()
    archive=HERE/'reading-compliance-colab.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as handle:
        for name,data in sorted(payload.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            handle.writestr(info,data)
    kit_sha=t.sha256(archive)
    cells=[cell('markdown', '''# Reading compliance: two bounded experiments
GPU access was refused by Colab usage limits during preparation. No new loss or quality results exist yet. This notebook executes only the approved fresh3-epoch LoRA runs (300 and600 examples), preserves all epoch checkpoints, and generates the current-adapter comparator plus six checkpoints on the same34 frozen inputs. No paid calls, purchases, test access, or UI adapter changes.

Select the existing free T4 runtime. The same FP16 precision and allocator setting apply to both runs. Stop on any failed gate. The existing completed historical adapter is used only as the evaluation comparator; both training runs start fresh. All data is independently agent-reviewed, with human review pending.
'''),cell('code',f'''import os, sys
assert 'torch' not in sys.modules, 'Restart session; allocator must precede torch import'
os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
from pathlib import Path
import hashlib, json, zipfile, subprocess
EXPECTED_KIT_SHA256={kit_sha!r}
KIT=Path('/content/{HERE.name}')
'''),cell('code',f'''# Upload reading-compliance-colab.zip, or use Colab Files sidebar before running this cell.
ARCHIVE=Path('/content/reading-compliance-colab.zip')
if not ARCHIVE.exists():
    from google.colab import files
    uploaded=files.upload()
    assert set(uploaded)=={{'reading-compliance-colab.zip'}}
    ARCHIVE.write_bytes(uploaded['reading-compliance-colab.zip'])
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==EXPECTED_KIT_SHA256
assert not KIT.exists(), 'Preserve existing kit; restart runtime for a fresh extraction'
with zipfile.ZipFile(ARCHIVE) as archive:
    assert len(archive.namelist())==len(set(archive.namelist()))
    assert archive.testzip() is None
    for info in archive.infolist():
        assert not Path(info.filename).is_absolute() and '..' not in Path(info.filename).parts
        assert (info.external_attr>>16)&0o170000 != 0o120000
    archive.extractall(KIT)
kit_manifest=json.loads((KIT/'kit-manifest.json').read_text())
assert set(archive.namelist())==set(kit_manifest['files'])|{{'kit-manifest.json'}}
for name,expected in kit_manifest['files'].items():
    assert hashlib.sha256((KIT/name).read_bytes()).hexdigest()==expected,name
STAGE=KIT/'stage1'
EXPERIMENT=STAGE/'experiments'/{HERE.name!r}
assert hashlib.sha256((EXPERIMENT/'plan.json').read_bytes()).hexdigest()==kit_manifest['plan_sha256']
'''),cell('code','''# Official registry pins; torch>=2.6 is required for safe optimizer/RNG resume.
# Reuse the hash-bound original dependency preflight ONLY, preserving its torchao safeguards.
TRAINING_MODE='lora'
legacy_notebook=json.loads((STAGE/'sft_colab.ipynb').read_text())
exec(compile(''.join(legacy_notebook['cells'][4]['source']),'reviewed-dependency-preflight','exec'))
subprocess.run([sys.executable,'-m','pip','install','-q','matplotlib'],check=True)
from packaging.version import Version
import torch
assert Version(torch.__version__.split('+')[0])>=Version('2.6')
assert torch.cuda.is_available() and torch.cuda.device_count()==1
assert 'T4' in torch.cuda.get_device_name(0), 'No automatic hardware substitution'
print(torch.__version__,torch.cuda.get_device_name(0))
'''),cell('code','''# Prefetch pinned tokenizer; existing CPU mask tests deliberately require local_files_only.
from transformers import AutoTokenizer
AutoTokenizer.from_pretrained('Qwen/Qwen3-1.7B',revision='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e')
# Offline integrity tests include real tiny CPU models; never load held-out files.
subprocess.run([sys.executable,'-m','unittest','discover','-s',str(STAGE),'-p','test_sft_train.py','-v'],check=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s',str(EXPERIMENT),'-p','test_*.py','-v'],check=True)
'''),cell('code',f'''from google.colab import drive
drive.mount('/content/drive')
OUTPUT=Path('/content/drive/MyDrive/Reading-Model/sft/{HERE.name}')
CURRENT_ADAPTER=Path('/content/drive/MyDrive/Reading-Model/sft/qwen-sft300-v2-lora-allocator-20261030-008/full/adapter')
assert CURRENT_ADAPTER.is_dir(), 'Locate the historical verified adapter; never substitute another adapter'
OUTPUT.mkdir(parents=True,exist_ok=True)
if not (OUTPUT/'dependency-preflight.json').exists():
    (OUTPUT/'dependency-preflight.json').write_text(json.dumps(PIP_CHECK_DIAGNOSTICS,indent=2)+'\\n')
# Explicit resume only: set BOTH only and exact latest complete epoch checkpoint.
ONLY=None # 'same300' or 'expanded600'
RESUME=None # exact OUTPUT/ONLY/full/checkpoints/checkpoint-N
'''),cell('code','''command=[sys.executable,str(EXPERIMENT/'execute.py'),'--plan',str(EXPERIMENT/'plan.json'),'--output',str(OUTPUT),'--current-adapter',str(CURRENT_ADAPTER)]
if ONLY is not None: command.extend(['--only',ONLY])
if RESUME is not None:
    assert ONLY is not None
    command.extend(['--resume',str(RESUME)])
# Fresh smoke per configuration; >=15% operational headroom; zero skipped updates.
# Stops preserve numerical/memory/integrity diagnostics. Never continue from old completed adapter.
subprocess.run(command,check=True)
'''),cell('code','''# Plot only real recorded update losses. Prior plots are never replaced.
for name in ('same300','expanded600'):
    full=OUTPUT/name/'full'
    if (full/'run-record.json').exists() and json.loads((full/'run-record.json').read_text())['status']=='training_completed':
        plot=OUTPUT/name/'loss-curves'
        if not plot.exists():
            subprocess.run([sys.executable,str(EXPERIMENT/'plot_results.py'),'loss','--full',str(full),'--out',str(plot)],check=True)
'''),cell('code','''# Conceal identity-key.json and all run paths from the independent reviewing agent.
# Supply only blind-review/review.jsonl + full prompt/rubric + REVIEW_PROTOCOL.md.
plan=json.loads((EXPERIMENT/'plan.json').read_text())
subprocess.run([sys.executable,str(EXPERIMENT/'evaluate.py'),'blind','--reference',str(EXPERIMENT/'frozen'),'--reference-sha',plan['frozen_manifest_sha256'],'--runs',str(OUTPUT/'review-runs.json'),'--out',str(OUTPUT/'blind-review')],check=True)
print('Raw generation complete. Independent blinded quality ratings and human review remain pending.')
'''),cell('markdown','''After independent ratings, use `evaluate.py summarize`, `plot_results.py pairs`, and `choose_checkpoint.py` as documented in README.md. A qualifying >=+20pp primary gain needs two more paired seeds on the same inputs, positive gain in both, and no new serious failures. Extra seeds are not independent cases. No automatic adapter replacement.

The fresh epoch-one checkpoint uses linear decay over114updates, unlike the historical38update schedule. The600row experiment has225updates and1800row exposures vs114updates/900exposures; it changes coverage and optimization exposure together.
''')]
    if preparation_only:
        cells[0]['source']=('''# Partial preparation: reading compliance experiment
Colab GPU access is blocked by usage limits. GPT-6.1 Sol/high authoring and independent review also hit account usage limits. The new corpus is incomplete and unapproved. This sealed notebook can execute ONLY the unchanged300-row three-epoch run when a freeT4 becomes available. The600-row run and adoption decision are blocked until the specified data and independent audit are complete.

It preserves epoch checkpoints, uses the verified current adapter as comparator, and evaluates only the34frozen development cases. No new results exist yet. No purchases, held-out test access, or live UI changes.
''').splitlines(keepends=True)
        cells[-1]['source']=('''The full experiment remains incomplete: expanded600 is absent from this sealed plan. Do not make an adoption decision from this partial package. Preserve these artifacts and prepare a new version only after all300new examples and original-corpus fixes receive independent review.
''').splitlines(keepends=True)
    notebook=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),colab=dict(provenance=[]),accelerator='GPU'),nbformat=4,nbformat_minor=5)
    t.write_json(HERE/'reading_compliance_colab.ipynb',notebook)
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
        assert set(handle.namelist())==set(payload)
        for name,data in payload.items(): assert handle.read(name)==data
    delivery=dict(status='partial_preparation_gpu_and_independent_review_blocked' if preparation_only else 'prepared_gpu_access_blocked',archive_sha256=kit_sha,notebook_sha256=t.sha256(HERE/'reading_compliance_colab.ipynb'),plan_sha256=t.sha256(HERE/'plan.json'),dataset_manifest_sha256=config.manifest_sha256 if config else None,expanded_data_approved=not preparation_only,frozen_manifest_sha256=frozen_sha,kit_files=len(payload),kit_bytes=archive.stat().st_size)
    t.write_json(HERE/'delivery.json',delivery)
    for name in ('plan.json','current-adapter-record.json','reading-compliance-colab.zip','reading_compliance_colab.ipynb','delivery.json'):
        (HERE/name).chmod(0o444)
    print(json.dumps(delivery,indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation-only',action='store_true',help='Seal only the approved unchanged300 run; expanded run/adoption remain blocked')
    build(parser.parse_args().preparation_only)
