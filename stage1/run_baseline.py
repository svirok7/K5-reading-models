"""Run controlled baseline generations, resumable per configuration."""
import hashlib
import argparse
import getpass
import importlib.metadata
import json
import os
import platform
import random
from pathlib import Path
from engine import ROOT, OpenAIEngine, ClaudeEngine, SarvamEngine, QwenEngine, digest, prompt_for

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--backend', choices=['sarvam','qwen','openai','claude'], required=True)
    p.add_argument('--split', choices=['dev','test'], default='dev')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--model', default='')
    p.add_argument('--adapter', default=None)
    p.add_argument('--out', required=True)
    p.add_argument('--frozen', action='store_true', help='Required for the test split')
    p.add_argument('--retry-errors', action='store_true')
    p.add_argument('--max-output-tokens', type=int, default=512)
    p.add_argument('--options', default='{}', help='OpenAI options JSON, e.g. temperature if supported')
    args = p.parse_args()
    if args.split == 'test' and not args.frozen:
        p.error('Freeze rubric/prompts/settings on dev, then use --frozen.')
    cases = [json.loads(x) for x in (ROOT/'data'/f'{args.split}.jsonl').read_text().splitlines()]
    if args.split == 'test':
        frozen = json.loads((ROOT/'data/benchmark-v2-manifest.json').read_text())
        actual = hashlib.sha256((ROOT/'data/test.jsonl').read_bytes()).hexdigest()
        if len(cases) != 50 or actual != frozen['sha256']:
            raise ValueError('Frozen 50-case benchmark changed. Review and version it before running.')
    if args.limit: cases = cases[:args.limit]
    if args.backend == 'openai':
        key = os.environ.get('OPENAI_API_KEY') or getpass.getpass('OpenAI API key (not saved): ')
        engine = OpenAIEngine(args.model, key, max_tokens=args.max_output_tokens, options=json.loads(args.options))
    elif args.backend == 'claude':
        key = os.environ.get('ANTHROPIC_API_KEY') or getpass.getpass('Anthropic API key (not saved): ')
        engine = ClaudeEngine(args.model, key, max_tokens=args.max_output_tokens)
    elif args.backend == 'qwen': engine = QwenEngine(adapter=args.adapter)
    else: engine = SarvamEngine(adapter=args.adapter)
    versions = {}
    for package in ['torch','transformers','accelerate','bitsandbytes','peft']:
        try: versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: pass
    manifest = {'engine': engine.metadata, 'split': args.split, 'case_hash': digest(cases),
        'prompt_hashes': {k:digest(prompt_for(k)) for k in ['A','B']},
        'rubric_hash': digest((ROOT/'RUBRIC.md').read_text()),
        'reader_profile_hash': digest(__import__('engine').reader_profile()), 'seed': 42,
        'python': platform.python_version(), 'platform': platform.platform(), 'packages': versions}
    fingerprint = digest(manifest)
    directory = Path(args.out).expanduser(); directory.mkdir(parents=True,exist_ok=True)
    meta = directory/f'{args.backend}-{args.split}-manifest.json'
    result_path = directory/f'{args.backend}-{args.split}.jsonl'
    if meta.exists() and json.loads(meta.read_text()) != manifest:
        raise ValueError('Run configuration changed. Choose a new output directory.')
    meta.write_text(json.dumps(manifest,indent=2)+'\n')
    prior = {}
    if result_path.exists():
        for line in result_path.read_text().splitlines():
            try: row=json.loads(line)
            except json.JSONDecodeError:
                raise ValueError('Incomplete JSONL line after interruption. Back up and remove only that last line before resuming.')
            if row.get('fingerprint') != fingerprint: raise ValueError('Result fingerprint mismatch.')
            prior[(row['case_id'],row['condition'])]=row
    jobs = [(case,condition) for case in cases for condition in ['A','B']]
    random.Random(42).shuffle(jobs)
    for case,condition in jobs:
        old = prior.get((case['id'],condition))
        if old and (old['status'] != 'error' or not args.retry_errors): continue
        row = {'case_id':case['id'], 'category':case['category'], 'messages':case['messages'],
            'expected_behavior':case['expected_behavior'], 'condition':condition,
            'benchmark_version':case.get('benchmark_version'), 'case_type':case.get('case_type','single_turn'),
            'meaningful_answer_check':case.get('meaningful_answer_check',case['expected_behavior']),
            'backend':args.backend, 'fingerprint':fingerprint, 'model':engine.metadata}
        try: row.update(engine.generate(prompt_for(condition),case['messages']))
        except Exception as exc:
            # Never print request headers, API keys, or full provider error payloads.
            row.update(status='error',error_type=type(exc).__name__,text='',latency_s=None)
        with result_path.open('a') as f:
            f.write(json.dumps(row,ensure_ascii=False)+'\n'); f.flush(); os.fsync(f.fileno())
        print(case['id'],condition,row['status'],flush=True)
    print('Saved:',result_path)

if __name__ == '__main__': main()
