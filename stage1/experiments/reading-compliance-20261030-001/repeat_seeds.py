"""Conditional two-seed confirmation for the selected qualifying checkpoint only."""
import argparse
import json
from pathlib import Path
import re
import evaluate
import execute

HERE=Path(__file__).resolve().parent


def run(output,current_adapter,primary_summary,primary_decision):
    output=Path(output)
    summary=json.loads(Path(primary_summary).read_text())
    decision=json.loads(Path(primary_decision).read_text())
    plan=json.loads((HERE/'plan.json').read_text())
    execute.check_plan(plan)
    if plan.get('pending_experiments'):
        raise ValueError('Full study incomplete; extra-seed adoption confirmation is blocked')
    if summary['seed_offset'] != 0 or summary['frozen_manifest_sha256'] != plan['frozen_manifest_sha256']:
        raise ValueError('Confirmation requires the sealed primary evaluation')
    selected=decision.get('selected')
    if decision.get('recommendation') != 'pending_repeat_seeds' or selected not in summary['results'] or not summary['results'][selected]['qualifies_for_repeat_seeds']:
        raise ValueError('No primary checkpoint qualified; do not launch follow-up experiments')
    match=re.fullmatch(r'(same300|expanded600)-epoch([1-3])',selected)
    if not match:
        raise ValueError('Unrecognized selected checkpoint')
    name,epoch=match.group(1),int(match.group(2))
    expected=next(row for row in plan['experiments'] if row['name']==name)
    step=epoch*((expected['config']['train_examples']+7)//8)
    if decision['checkpoint'] != {'epoch':epoch,'updates':step}:
        raise ValueError('Decision epoch/update metadata differs')
    full=output/name/'full'
    record=json.loads((full/'run-record.json').read_text())
    if record['status'] != 'training_completed':
        raise ValueError('Selected training run is incomplete')
    checkpoint=full/'checkpoints'/f'checkpoint-{step}'
    checkpoint_sha=record['checkpoint_index'][checkpoint.name]['resume_record_sha256']
    if summary['candidate_record_hashes'][selected] != checkpoint_sha or summary['candidate_record_hashes']['current'] != plan['current_adapter_record_sha256']:
        raise ValueError('Selected/current adapter binding changed')
    for offset in (1000003,2000003):
        root=output/f'repeat-seed-{offset}'
        root.mkdir(exist_ok=False)
        runs={}
        for label,adapter,record_path,record_sha in (
            ('current',Path(current_adapter),HERE/'current-adapter-record.json',plan['current_adapter_record_sha256']),
            (selected,checkpoint,checkpoint/'resume-record.json',checkpoint_sha)):
            destination=root/label
            evaluate.generate(HERE/'frozen',plan['frozen_manifest_sha256'],adapter,record_path,record_sha,destination,offset,expected_model_artifacts=plan['prepared_model_artifacts'])
            runs[label]=str(destination)
        evaluate.write(root/'review-runs.json',runs)
        evaluate.blind(HERE/'frozen',plan['frozen_manifest_sha256'],runs,root/'blind-review')
    print('Both repeat generations ready for independent concealed review. No adoption or UI change yet.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--current-adapter',type=Path,required=True)
    parser.add_argument('--primary-summary',type=Path,required=True)
    parser.add_argument('--primary-decision',type=Path,required=True)
    a=parser.parse_args()
    run(a.output,a.current_adapter,a.primary_summary,a.primary_decision)
