"""One-time immutable export after independent exact-hash final approval."""
import json,shutil,sys,datetime
from pathlib import Path
import build_corpus as b
from validate_export import validate
A=Path(__file__).resolve().parent;EXP=A.parent;ROOT=b.ROOT

def seal(approval_path):
 src=A/'final-candidate';dst=ROOT/'datasets/sft-600-v1'
 if dst.exists():
  print(json.dumps(validate(dst,True),indent=2));return
 report=json.loads(approval_path.read_text())
 assert report['status']=='approved'and report['human_approved']is False
 for name,digest in report['files'].items():
  assert digest==b.sha(src/name),(name,digest,b.sha(src/name))
 result=validate(src)
 assert report['rows']==600 and report['open_findings']==[]
 per_row_path=approval_path.with_name('final600-independent-approval.jsonl')
 per_row=[json.loads(line)for line in per_row_path.read_text().splitlines()]
 assert len(per_row)==600 and all(x['semantic_review']=='pass'and x['reading_review']=='pass'and x['full_context_review']=='pass'and all(w['eligible']for w in x['word_evidence'])for x in per_row)
 dst.mkdir()
 for p in src.iterdir():
  if p.is_file():shutil.copy2(p,dst/p.name)
 shutil.copy2(approval_path,dst/'audit.json')
 shutil.copy2(per_row_path,dst/'audit-rows.jsonl')
 shutil.copy2(approval_path.with_name('final600-history-annotation-check.jsonl'),dst/'audit-history.jsonl')
 shutil.copy2(EXP/'audit/original-three-corrections-independent-approval.jsonl',dst/'original-changes-independent-approval.jsonl')
 (dst/'audit.md').write_text('All 600 final completions passed independent semantic and linguistic review. The final audit binds the exact SFT, metadata, and historical-flaw sidecar hashes. Original rows 32, 45, and 65 changed; the other 297 original records remain unchanged. The six new batches contain 50 examples each. All 300 new examples were reviewed individually, and each batch used at most two audit rounds. Human approval remains pending.\n')
 (dst/'README.md').write_text('sft-600-v1 contains the independently reviewed successor to sft-300-v2: 300 original examples, with three explicit semantic repairs, plus 300 newly authored examples.\n\nOnly prompt and completion appear in sft.jsonl. The system message is the complete current condition-B reading prompt. Historical assistant turns, including explicitly annotated semantic and reading-profile defects, are input only. Only the final completion is supervised. Metadata and sound/list evidence live in review.jsonl; complete historical word findings live in history-flaws.jsonl and history-lexicon.json.\n\nThe new examples have six primary categories of 50 each, exactly 150 history-required rows, 150 rows with 3–5 prior assistant turns, and 64 rows with intentional semantic recovery. Including lexical history defects, 143 new rows have explicitly annotated history flaws. The other 150 new rows use self-contained child requests or multi-event accounts.\n\nThe final independent audit is audit.json. changes.jsonl preserves exact before/after original repairs. provenance.json binds all seven approved source artifacts and their independent reports. All artifacts are hashed in manifest.json and the manifest is hashed separately. Files are read-only; create a new dataset version for further changes. Human approval is false. Training and GPU execution are separate tasks, with no model-quality claim in this dataset release.\n')
 (dst/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
 sources=json.loads((dst/'provenance.json').read_text())
 artifact_names=sorted(p.name for p in dst.iterdir()if p.is_file())
 manifest={'version':'sft-600-v1','count':600,'source_dataset':'datasets/sft-300-v2','source_sft_sha256':sources['baseline_sft_sha256'],'source_review_sha256':sources['baseline_review_sha256'],'original_row_count':300,'new_row_count':300,'changed_ids':['pilot-032','pilot-045','pilot-065'],'unchanged_original_row_count':297,'change_log':'changes.jsonl','change_log_sha256':b.sha(dst/'changes.jsonl'),'frozen_data':True,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'audit_status':'independently_reviewed_pending_human','review_status':'independently_reviewed_pending_human','human_approved':False,'tokenization_verified':False,'training_executed':False,'audit_report':'audit.json','audit_summary':'audit.md','audit':{'auditor':{'agent_id':'/root/reviewer','model':'gpt-6.1-sol','reasoning_effort':'high'},'examples_reviewed':600,'pass':600,'open_findings':0,'sft_sha256':b.sha(dst/'sft.jsonl'),'review_sha256':b.sha(dst/'review.jsonl'),'report_sha256':b.sha(dst/'audit.json')},'new_category_counts':result['new_category_counts'],'new_history_rows':result['new_history_required'],'new_3_to_5_prior_assistant_turns':result['new_3_to_5_prior_assistant_turns'],'new_intentional_semantic_flawed_rows':result['new_intentional_semantic_flawed_rows'],'new_rows_with_any_annotated_history_flaw':result['new_rows_with_any_annotated_history_flaw'],'supervision':'final_completion_only','spec_sha256':b.sha(ROOT/'READER_PROFILE.txt'),'expanded_prompt_sha256':__import__('hashlib').sha256(__import__('engine').prompt_for('B').encode()).hexdigest(),'artifacts':{name:b.sha(dst/name)for name in artifact_names}}
 (dst/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(dst/'manifest.sha256').write_text(b.sha(dst/'manifest.json')+'  manifest.json\n')
 checked=validate(dst,True)
 for p in dst.iterdir():
  if p.is_file():p.chmod(0o444)
 print(json.dumps({'export':str(dst),'manifest_sha256':b.sha(dst/'manifest.json'),**checked},indent=2))
if __name__=='__main__':seal(Path(sys.argv[1]))
