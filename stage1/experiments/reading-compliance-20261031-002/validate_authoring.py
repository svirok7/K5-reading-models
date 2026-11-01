"""Validate saved authoring progress without granting semantic approval.
Use --require-complete before exporting the proposed600-row successor.
"""
from collections import Counter
import json
from pathlib import Path
import re
import sys
import evaluate

HERE=Path(__file__).resolve().parent
CATEGORIES=['meaning_preserving_explanation','exact_forms_lexical_boundaries','corrections_refusals_topic_changes','honest_identity_personal_experience','emotional_support_safe_relevant_help','long_history_tracking_recovery']


def validate():
    sources=[]; totals=Counter(); categories=Counter(); approved=0; details=[]
    frozen_rows=evaluate.rows(HERE/'frozen'/'cases.jsonl')
    frozen_inputs={evaluate.canonical(row['messages']) for row in frozen_rows}
    for batch in range(1,7):
        folder=HERE/'authoring'/f'batch-{batch:02d}'
        if not (folder/'sft.jsonl').exists():
            details.append(dict(batch=batch,status='not_authored',count=0));continue
        data=evaluate.rows(folder/'sft.jsonl');meta=evaluate.rows(folder/'review.jsonl')
        if len(data) != 50 or len(meta) != 50:
            raise ValueError('Each present batch must contain50 complete paired records')
        expected_category=CATEGORIES[batch-1]
        for row,record in zip(data,meta):
            if set(row) != {'prompt','completion'} or len(row['completion']) != 1 or row['completion'][0]['role'] != 'assistant':
                raise ValueError('Only final-completion training fields allowed')
            messages=row['prompt'][1:]
            if row['prompt'][0] != {'role':'system','content':frozen_rows[0]['prompt']} or messages != record['context_messages'] or row['completion'][0]['content'] != record['target_response']:
                raise ValueError('Training/review prompt, target, or history mismatch')
            if not messages or messages[-1]['role'] != 'user' or any(m['role'] != ('user' if i%2==0 else 'assistant') for i,m in enumerate(messages)):
                raise ValueError('Malformed alternating history')
            if evaluate.canonical(messages) in frozen_inputs:
                raise ValueError('Exact frozen evaluation history copied into training')
            if record['category'] != expected_category or record['requires_history'] != (len(messages)>1):
                raise ValueError('Incorrect category/history annotation')
            assistant_turns=sum(m['role']=='assistant' for m in messages)
            flaws=record['flawed_history_indices']
            if len(flaws) != len(set(flaws)) or any(type(i) is not int or not 1<=i<=len(messages) or messages[i-1]['role']!='assistant' for i in flaws):
                raise ValueError('Invalid flawed prior assistant annotation')
            if len(record.get('historical_flaws',[])) != len(flaws) or record['supervision'] != 'final_completion_only':
                raise ValueError('Historical flaws must be explicitly annotated and input-only')
            tokens=set(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?|[0-9]+",record['target_response'].lower()))
            missing=tokens-set(record['lexical_evidence'])
            totals['missing_word_evidence']+=len(missing)
            totals['history_rows']+=len(messages)>1
            totals['three_to_five_prior_assistant_turns']+=3<=assistant_turns<=5
            totals['flawed_history_rows']+=bool(flaws)
            categories[expected_category]+=1
        sft_sha=evaluate.sha(folder/'sft.jsonl');review_sha=evaluate.sha(folder/'review.jsonl')
        summaries=sorted((HERE/'audit').glob(f'batch-{batch:02d}-round-*-summary.json'))
        valid=[]
        for path in summaries:
            summary=json.loads(path.read_text())
            if summary['source_sft_sha256']==sft_sha and summary['source_review_sha256']==review_sha:
                valid.append(summary)
        last=max(valid,key=lambda r:r['round']) if valid else None
        is_approved=bool(last and last['status']=='approved' and last['rows_reviewed']==50 and last['pass_count']==50 and not last['revision_case_indices_1based'])
        if is_approved: approved+=50
        details.append(dict(batch=batch,count=50,status='independently_approved_pending_human' if is_approved else 'pending_independent_approval',sft_sha256=sft_sha,review_sha256=review_sha,latest_matching_round=last['round'] if last else None,open_case_indices=last['revision_case_indices_1based'] if last else None))
        sources.extend(data)
    complete=len(sources)==300 and approved==300 and totals['history_rows']==150 and totals['three_to_five_prior_assistant_turns']>=100 and totals['flawed_history_rows']>=50 and totals['missing_word_evidence']==0 and all(categories[c]==50 for c in CATEGORIES)
    return dict(new_examples_authored=len(sources),new_examples_independently_approved=approved,remaining_examples_to_author=300-len(sources),new_example_counts=dict(totals),category_counts=dict(categories),batches=details,complete_and_approved=complete,human_approved=False,original_corpus_fixes_materialized=False,final600_exported=False,limitations='Structural checks do not grant linguistic or semantic approval. Original32/45/65 fixes must be materialized with independently bound before/after records before export.')


if __name__=='__main__':
    report=validate()
    print(json.dumps(report,indent=2))
    if '--require-complete' in sys.argv and not report['complete_and_approved']:
        raise SystemExit('Blocked: requested300new examples and independent approval/quotas are incomplete')
