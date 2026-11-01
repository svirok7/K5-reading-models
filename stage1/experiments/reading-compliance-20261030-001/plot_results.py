"""Plot saved real update losses and export blinded-review paired examples.
No synthetic training metrics; never overwrite an existing artifact.
"""
import argparse
import csv
import json
import math
import hashlib
import sys
from pathlib import Path


def loss_plot(full, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    full, out = Path(full), Path(out)
    out.mkdir(parents=True,exist_ok=False)
    record = json.loads((full/'run-record.json').read_text())
    if record['status'] != 'training_completed':
        raise ValueError('Only verified completed runs can be plotted')
    logs = json.loads((full/'trainer-log.json').read_text())
    points = [row for row in logs if 'loss' in row]
    if len(points) != record['optimizer_steps'] or sorted(row['step'] for row in points) != list(range(1,record['optimizer_steps']+1)):
        raise ValueError('Expected exactly one real loss record per optimizer update')
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import sft_train
    name=f"checkpoint-{record['optimizer_steps']}"
    checkpoint=full/'checkpoints'/name
    sft_train.verify_replay_checkpoint(checkpoint,record['checkpoint_index'][name]['resume_record_sha256'],record['identity'])
    bound_logs=json.loads((checkpoint/'trainer_state.json').read_text())['log_history']
    bound_points=[row for row in bound_logs if 'loss' in row]
    if points != bound_points or any(not math.isfinite(float(row['loss'])) or not math.isfinite(float(row['learning_rate'])) for row in points):
        raise ValueError('Loss log differs from retained hash-bound checkpoint or contains nonfinite values')
    if [{k:row[k] for k in ('step','loss','learning_rate')} for row in points] != record['training_ledger']['updates']:
        raise ValueError('Loss log differs from audited per-update ledger')
    with (out/'training-loss.csv').open('x') as handle:
        writer = csv.DictWriter(handle,fieldnames=['step','epoch','loss','learning_rate'])
        writer.writeheader()
        writer.writerows({key:point.get(key) for key in writer.fieldnames} for point in points)
    fig, axis = plt.subplots(figsize=(9,4.5))
    axis.plot([r['step'] for r in points],[r['loss'] for r in points],linewidth=1.3)
    axis.set(xlabel='Applied optimizer update',ylabel='Completion training loss',title=f"{record['train_examples']} examples, {record['config']['epochs']} epochs")
    for epoch in range(1,record['config']['epochs']+1):
        axis.axvline(epoch*((record['train_examples']+7)//8),color='gray',linewidth=.7,linestyle='--')
    axis.grid(alpha=.15)
    fig.tight_layout()
    fig.savefig(out/'training-loss.png',dpi=180)
    plt.close(fig)


def paired_examples(review, summary, out):
    review, out = Path(review),Path(out)
    if out.exists():
        raise ValueError('Preserve previous paired report')
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    manifest=json.loads((review/'manifest.json').read_text())
    if sha(review/'review.jsonl') != manifest['review_sha256'] or sha(review/'identity-key.json') != manifest['identity_key_sha256']:
        raise ValueError('Blinded review artifacts changed')
    key = json.loads((review/'identity-key.json').read_text())
    raw = [json.loads(line) for line in (review/'review.jsonl').read_text().splitlines()]
    responses = {(key[row['review_id']]['variant'],key[row['review_id']]['case_id']):row for row in raw}
    summary = json.loads(Path(summary).read_text())
    if summary['review_manifest_sha256'] != sha(review/'manifest.json') or summary['frozen_manifest_sha256'] != manifest['frozen_manifest_sha256'] or summary['candidate_record_hashes'] != manifest['candidate_record_hashes'] or summary['seed_offset'] != manifest['inference_group']['seed_offset'] or summary['comparison_group'] != {k:v for k,v in manifest['inference_group'].items() if k!='seed_offset'}:
        raise ValueError('Summary belongs to a different frozen review/seed/checkpoint group')
    reference = summary['reference']
    output = ['# Paired gains and regressions','', 'Fixed histories assess the next turn only. All responses below are raw.','']
    for variant,result in summary['results'].items():
        if variant == reference:
            continue
        output += [f'## {variant}','']
        for direction,field in [('Gains','paired_gains'),('Regressions','paired_regressions')]:
            output += [f'### {direction}','']
            if not result[field]:
                output += ['None on this seed.','']
            for case_id in result[field]:
                before,after = responses[reference,case_id],responses[variant,case_id]
                output += [f'Case `{case_id}` ({after["history_kind"]})','', '```json',json.dumps(after['messages'],ensure_ascii=False,indent=2),'```','',f'Current: {before["text"]}','',f'Candidate: {after["text"]}','']
    out.write_text('\n'.join(output)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    loss=sub.add_parser('loss')
    loss.add_argument('--full',type=Path,required=True)
    loss.add_argument('--out',type=Path,required=True)
    pairs=sub.add_parser('pairs')
    pairs.add_argument('--review',type=Path,required=True)
    pairs.add_argument('--summary',type=Path,required=True)
    pairs.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.command=='loss': loss_plot(a.full,a.out)
    else: paired_examples(a.review,a.summary,a.out)
