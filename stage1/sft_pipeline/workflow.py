#!/usr/bin/env python3
"""Disk-backed SFT review gates. Python 3 standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
CHECKS = ('word_eligibility', 'reasoning_accuracy', 'meaningfulness', 'history_use')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_read(path):
    return json.loads(Path(path).read_text())


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    os.replace(temp, path)


def rows(path):
    parsed = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    require(all(isinstance(r, dict) for r in parsed), f'JSONL rows must be objects: {path}')
    return parsed


def require(ok, message):
    if not ok:
        raise ValueError(message)


def words(text):
    return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", text.lower())


class Workflow:
    def __init__(self, root=HERE.parent, work=HERE):
        self.root = Path(root).resolve()
        self.work = Path(work).resolve()
        self.frozen = self.work / 'frozen'
        self.state_path = self.work / 'state.json'
        config_path = self.frozen / 'spec.json' if (self.frozen / 'spec.json').exists() else self.work / 'spec.json'
        self.config = json_read(config_path)
        self.batch_config = {b['batch']: b for b in self.config['batches']}
        self.batches = tuple(self.batch_config)
        require(bool(self.batches) and len(self.batches) == len(self.config['batches']), 'Unique configured batches required')
        for batch, settings in self.batch_config.items():
            require(re.fullmatch(r'[0-9]{3}', batch) is not None, 'Batch labels must be three digits')
            first, last = self.id_number(settings['first_id']), self.id_number(settings['last_id'])
            require(last - first + 1 == settings['count'] and settings['count'] > 0, 'Invalid batch ID range/count')
        self.baseline_count = self.config.get('baseline_count', self.id_number(self.config['batches'][0]['first_id']) - 1)
        self.output_count = self.config.get('destination_count', self.baseline_count + sum(b['count'] for b in self.config['batches']))
        require(self.output_count == self.baseline_count + sum(b['count'] for b in self.config['batches']), 'Destination count disagrees with source counts')
        for key in ('baseline', 'destination'):
            value = Path(self.config[key])
            require(not value.is_absolute() and len(value.parts) == 2 and value.parts[0] == 'datasets'
                    and value.parts[1] not in ('.', '..'), 'Dataset paths must be direct children of datasets')
        self.baseline = self.root / self.config['baseline']
        self.destination = self.root / self.config['destination']
        require(self.baseline != self.destination, 'Baseline and destination must differ')

    @staticmethod
    def id_number(value):
        require(isinstance(value, str) and re.fullmatch(r'pilot-[0-9]+', value) is not None, 'IDs must use pilot-NNN format')
        return int(value.split('-')[1])

    def init(self):
        if self.state_path.exists():
            self.verify()
            return self.status()
        require(not (self.frozen / 'manifest.json').exists(),
                'Frozen manifest exists without state; restore state from backup, do not refreeze.')
        baseline = self.baseline
        require(len(rows(baseline / 'sft.jsonl')) == self.baseline_count, f'Baseline must have {self.baseline_count} rows')
        require(len(rows(baseline / 'review.jsonl')) == self.baseline_count, f'Baseline review must have {self.baseline_count} rows')
        self.frozen.mkdir(parents=True, exist_ok=True)
        sources = {'READER_PROFILE.txt': self.root / 'READER_PROFILE.txt',
                   'RUBRIC.md': self.root / 'RUBRIC.md',
                   'dolch-through-grade1.json': self.root / 'data/dolch-through-grade1.json',
                   'spec.json': self.work / 'spec.json',
                   'GENERATOR.md': self.work / 'GENERATOR.md',
                   'AUDITOR.md': self.work / 'AUDITOR.md'}
        for name, source in sources.items():
            shutil.copyfile(source, self.frozen / name)
        system = rows(baseline / 'sft.jsonl')[0]['prompt'][0]['content']
        (self.frozen / 'system.txt').write_text(system)
        # Only named baseline files at this level; never traverse archives or benchmark data.
        base_hashes = {p.name: digest(p) for p in sorted(baseline.iterdir()) if p.is_file()}
        manifest = {'version': 1, 'baseline': base_hashes,
                    'spec_files': {p.name: digest(p) for p in sorted(self.frozen.iterdir()) if p.is_file()}}
        atomic(self.frozen / 'manifest.json', manifest)
        state = {'version': 1, 'created_at': self.now(),
                 'frozen_manifest_sha256': digest(self.frozen / 'manifest.json'), 'batches': {}}
        self.save(state)
        return self.status()

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def save(self, state):
        atomic(self.state_path, state)

    def verify(self):
        require(self.state_path.exists(), 'Run init first')
        state = json_read(self.state_path)
        require(digest(self.frozen / 'manifest.json') == state['frozen_manifest_sha256'],
                'Frozen manifest changed')
        manifest = json_read(self.frozen / 'manifest.json')
        for name, sha in manifest['spec_files'].items():
            require(digest(self.frozen / name) == sha, f'Frozen specification changed: {name}')
        baseline = self.baseline
        for name, sha in manifest['baseline'].items():
            require(digest(baseline / name) == sha, f'Frozen baseline changed: {name}')
        return state

    def path(self, batch):
        require(batch in self.batches, f'Batch must be one of {self.batches}')
        return self.root / 'datasets' / ('synthetic-batch-' + batch)

    def hashes(self, batch):
        return {name + '_sha256': digest(self.path(batch) / (name + '.jsonl'))
                for name in ('sft', 'review')}

    def current(self, batch, record):
        try:
            return self.hashes(batch) == record.get('hashes')
        except FileNotFoundError:
            return False

    def require_previous(self, state, batch):
        require(batch in self.batches, f'Batch must be one of {self.batches}')
        for previous in self.batches[:self.batches.index(batch)]:
            prior = state['batches'].get(previous, {})
            require(prior.get('status') == 'accepted' and self.current(previous, prior),
                    f'Batch {previous} must be accepted at its current disk hashes before batch {batch}')
            self.check_audit(previous, prior)

    def start(self, batch, generator_agent, correction=False, generator_model=None, generator_reasoning=None):
        state = self.verify()
        self.require_previous(state, batch)
        require(generator_agent.strip(), 'Generator agent identity is required')
        generator_agent = generator_agent.strip()
        generator = self.config.get('generator')
        if generator:
            require(generator_model == generator['model'] and generator_reasoning == generator['reasoning_effort'],
                    'Generator must attest configured model and reasoning effort')
        old = state['batches'].get(batch)
        if old and not correction:
            require(old['generator_agent'] == generator_agent, 'Generator identity changed')
            return self.status()
        if old:
            require(old['generator_agent'] == generator_agent, 'Correction must retain generator identity')
            require(old['status'] != 'accepted' or not self.current(batch, old),
                    'Accepted unchanged batch needs no correction')
            round_number = old['correction_round'] + 1
            require(round_number <= self.config.get('correction_round_limit', 3), 'Maximum three correction rounds exhausted; batch remains blocked')
        else:
            require(not correction, 'Cannot correct a batch that has not started')
            round_number = 0
        state['batches'][batch] = {'status': 'started', 'generator_agent': generator_agent,
                                   'correction_round': round_number, 'started_at': self.now()}
        if generator:
            state['batches'][batch]['generator'] = {'model': generator_model, 'reasoning_effort': generator_reasoning}
        self.save(state)
        return state['batches'][batch]

    def structural(self, batch, state):
        sft, review = rows(self.path(batch) / 'sft.jsonl'), rows(self.path(batch) / 'review.jsonl')
        errors = []
        def check(ok, msg):
            if not ok:
                errors.append(msg)
        count = self.batch_config[batch]['count']
        check(len(sft) == count and len(review) == count, f'Expected exactly {count} aligned rows')
        system = (self.frozen / 'system.txt').read_text()
        first = self.id_number(self.batch_config[batch]['first_id'])
        expected_ids = [f'pilot-{n:03}' for n in range(first, first + count)]
        check([r.get('id') for r in review] == expected_ids, 'IDs/order differ from reserved batch range')
        history_count = self.config['requires_history_per_batch']
        check(sum(r.get('requires_history') is True for r in review) == history_count, f'Expected {history_count} requires_history=true')
        for bucket in ('short', 'medium', 'long'):
            count = self.config['input_length'][bucket]['count']
            check(sum(r.get('input_length_bucket') == bucket for r in review) == count,
                  f'Expected {count} {bucket} inputs')
        previous = rows(self.baseline / 'sft.jsonl')
        for prior in self.batches[:self.batches.index(batch)]:
            previous += rows(self.path(prior) / 'sft.jsonl')
        seen_rows = {json.dumps(r, sort_keys=True) for r in previous}
        seen_targets = {r['completion'][0]['content'].strip().casefold() for r in previous}
        baseline_review_keys = set(rows(self.baseline / 'review.jsonl')[0])
        dolch = {w.lower() for group in json_read(self.frozen / 'dolch-through-grade1.json')['groups'].values() for w in group}
        for index, (s, r) in enumerate(zip(sft, review)):
            tag = r.get('id', f'row-{index+1}')
            check(baseline_review_keys <= set(r), f'{tag}: baseline review fields missing: {sorted(baseline_review_keys - set(r))}')
            check(set(s) == {'prompt', 'completion'}, f'{tag}: SFT keys must only be prompt/completion')
            prompt, completion = s.get('prompt', []), s.get('completion', [])
            if not (isinstance(prompt, list) and isinstance(completion, list)
                    and all(isinstance(m, dict) for m in prompt + completion)):
                errors.append(f'{tag}: prompt/completion must be lists of message objects')
                continue
            check(isinstance(prompt, list) and len(prompt) >= 2, f'{tag}: prompt missing')
            check(completion and len(completion) == 1 and completion[0].get('role') == 'assistant', f'{tag}: completion must be one assistant message')
            if not prompt or not completion:
                continue
            check(prompt[0] == {'role': 'system', 'content': system}, f'{tag}: system mismatch')
            for j, message in enumerate(prompt[1:]):
                check(set(message) == {'role', 'content'} and isinstance(message.get('content'), str) and bool(message.get('content', '').strip()), f'{tag}: invalid message')
                check(message.get('role') == ('user' if j % 2 == 0 else 'assistant'), f'{tag}: roles must alternate')
            check(prompt[-1].get('role') == 'user', f'{tag}: prompt must end with user')
            check(prompt[1:] == r.get('context_messages'), f'{tag}: context alignment mismatch')
            target = completion[0].get('content', '')
            check(isinstance(target, str) and bool(target.strip()), f'{tag}: empty target')
            if not isinstance(target, str):
                continue
            check(set(completion[0]) == {'role', 'content'}, f'{tag}: completion fields invalid')
            check(target == r.get('target_response'), f'{tag}: target alignment mismatch')
            check(type(r.get('requires_history')) is bool, f'{tag}: requires_history must be bool')
            check(r.get('requires_history') == any(m.get('role') == 'assistant' for m in prompt[1:]), f'{tag}: requires_history must match assistant history presence')
            check(target.count('?') <= 1, f'{tag}: target has more than one question')
            assistant_texts = [target] + [m.get('content', '') for m in prompt[1:] if m.get('role') == 'assistant']
            for text in assistant_texts:
                if isinstance(text, str):
                    check(all(len(words(sentence)) <= 12 for sentence in re.split(r'[.!?]+', text) if sentence.strip()), f'{tag}: assistant sentence exceeds 12 words')
            if not isinstance(prompt[-1].get('content'), str):
                continue
            n = len(prompt[-1].get('content', '').split())
            bucket = next((b for b in ('short', 'medium', 'long') if n >= self.config['input_length'][b]['min'] and n <= self.config['input_length'][b].get('max', float('inf'))), None)
            check(n > 0 and r.get('input_length_bucket') == bucket, f'{tag}: final input bucket mismatch ({n} whitespace words)')
            check(isinstance(r.get('word_choice_reasoning'), str) and bool(r.get('word_choice_reasoning', '').strip()), f'{tag}: reasoning missing')
            check(bool(r.get('category')) and bool(r.get('scenario_family')), f'{tag}: category/scenario missing')
            checks = r.get('review_checks', {})
            if not isinstance(checks, dict):
                errors.append(f'{tag}: review_checks must be object')
                continue
            check(checks.get('unresolved_words') == [], f'{tag}: unresolved words must be explicitly empty')
            check(checks.get('human_approved') is False, f'{tag}: do not claim human approval')
            evidence = r.get('lexical_evidence', {})
            if not isinstance(evidence, dict):
                errors.append(f'{tag}: lexical_evidence must be object')
                continue
            required_words = set(words(target))
            for message in prompt[1:]:
                if message.get('role') == 'assistant':
                    required_words.update(words(message.get('content', '')))
            check(isinstance(evidence, dict) and required_words <= set(evidence), f'{tag}: evidence missing for target/history words: {sorted(required_words - set(evidence))}')
            for word in required_words & set(evidence):
                rationale = evidence[word]
                check(isinstance(rationale, str) and bool(rationale.strip()), f'{tag}: empty evidence for {word}')
                if isinstance(rationale, str) and 'dolch' in rationale.lower():
                    check(word in dolch, f'{tag}: false exact-Dolch claim: {word}')
            serial = json.dumps(s, sort_keys=True)
            check(serial not in seen_rows, f'{tag}: duplicate full row')
            check(target.strip().casefold() not in seen_targets, f'{tag}: duplicate target')
            seen_rows.add(serial)
            seen_targets.add(target.strip().casefold())
        return errors

    def validate(self, batch):
        state = self.verify()
        self.require_previous(state, batch)
        require(batch in state['batches'], 'Start batch before validation')
        record = state['batches'][batch]
        if record['status'] in ('audited', 'accepted') and self.current(batch, record):
            self.check_audit(batch, record)
            return {'status': record['status'], 'errors': [], 'hashes': record['hashes'],
                    'spec_sha256': state['frozen_manifest_sha256']}
        if record.get('hashes') and not self.current(batch, record):
            require(record['status'] == 'started', 'Files changed after validation; start --correction before revalidating')
        errors = self.structural(batch, state)
        record.update(status='validation_failed' if errors else 'validated', hashes=self.hashes(batch),
                      validated_at=self.now(), errors=errors)
        record.pop('audit', None)
        atomic(self.work / 'checkpoints' / batch / f'round-{record["correction_round"]}-validation.json', record)
        self.save(state)
        return {'status': record['status'], 'hashes': record['hashes'], 'errors': errors,
                'spec_sha256': state['frozen_manifest_sha256'],
                'note': 'Structural/evidence coverage only; semantic and phonics review require independent auditor.'}

    def validate_audit(self, batch, record, report):
        require(report.get('batch') == batch, 'Audit batch mismatch')
        require(report.get('spec_sha256') == digest(self.frozen / 'manifest.json'), 'Stale audit specification hash')
        for key, sha in self.hashes(batch).items():
            require(report.get(key) == sha == record['hashes'][key], f'Stale audit {key}')
        auditor = report.get('auditor', {})
        require(auditor.get('model') == 'gpt-6.1-sol' and auditor.get('reasoning_effort') == 'high', 'Auditor must attest gpt-6.1-sol/high')
        require(isinstance(auditor.get('agent_id'), str) and bool(auditor['agent_id'].strip())
                and auditor['agent_id'].strip() != record['generator_agent'], 'Auditor must be a distinct agent')
        actual_ids = [r['id'] for r in rows(self.path(batch) / 'review.jsonl')]
        examples = report.get('examples', [])
        require(len(examples) == self.batch_config[batch]['count'] and [e.get('id') for e in examples] == actual_ids, 'Audit requires all configured per-example verdicts in order')
        blocked = []
        for example in examples:
            require(example.get('verdict') in ('pass', 'fail'), 'Invalid audit verdict')
            require(isinstance(example.get('findings'), list), 'Findings must be explicit list')
            checks = example.get('checks', {})
            require(set(checks) == set(CHECKS) and all(type(v) is bool for v in checks.values()), 'Every audit check must be explicit bool')
            unresolved = False
            for finding in example['findings']:
                require(all(finding.get(k) for k in ('id', 'severity', 'status', 'detail')), 'Incomplete finding')
                require(finding['severity'] in ('low', 'medium', 'high'), 'Invalid finding severity')
                require(finding['status'] in ('open', 'resolved'), 'Invalid finding status')
                unresolved |= finding['status'] == 'open'
            if example['verdict'] != 'pass' or not all(checks.values()) or unresolved:
                blocked.append(example['id'])
        return blocked

    def audit(self, batch, audit_file):
        state = self.verify()
        self.require_previous(state, batch)
        record = state['batches'].get(batch, {})
        require(record.get('status') in ('validated', 'audit_failed', 'audited'), 'Validate before submitting audit')
        require(self.current(batch, record), 'Stale validation; correction and revalidation required')
        report = json_read(audit_file)
        blocked = self.validate_audit(batch, record, report)
        destination = self.work / 'checkpoints' / batch / f'round-{record["correction_round"]}-audit.json'
        require(not destination.exists(), 'An audit is already recorded for this round; use start --correction')
        atomic(destination, report)
        record.update(status='audit_failed' if blocked else 'audited',
                      audit={'path': str(destination.relative_to(self.work)), 'sha256': digest(destination)},
                      blocked_ids=blocked)
        self.save(state)
        return record

    def check_audit(self, batch, record):
        require(self.current(batch, record), 'Batch files changed; approval is stale')
        info = record.get('audit', {})
        require(bool(info.get('path')), 'No independent audit')
        path = self.work / info['path']
        require(digest(path) == info['sha256'], 'Stored audit changed')
        require(not self.validate_audit(batch, record, json_read(path)), 'Unresolved audit findings block acceptance')

    def accept(self, batch):
        state = self.verify()
        self.require_previous(state, batch)
        record = state['batches'].get(batch, {})
        require(record.get('status') in ('audited', 'accepted'), 'A passing independent audit is required')
        self.check_audit(batch, record)
        # Re-run structural checks at the same exact hashes before accepting.
        require(not self.structural(batch, state), 'Structural validation no longer passes')
        if record['status'] == 'accepted':
            return record
        record.update(status='accepted', accepted_at=self.now(), review_status='independent_model_reviewed_pending_human')
        self.save(state)
        return record

    def export(self, destination=None):
        state = self.verify()
        for batch in self.batches:
            require(state['batches'].get(batch, {}).get('status') == 'accepted', f'Batch {batch} is not accepted')
            self.check_audit(batch, state['batches'][batch])
            require(not self.structural(batch, state), f'Batch {batch} validation failed')
        destination = Path(destination) if destination else self.destination
        require(destination.resolve() != self.baseline.resolve(), 'Never overwrite baseline')
        source_dirs = [self.baseline] + [self.path(b) for b in self.batches]
        payload = {}
        for name in ('sft.jsonl', 'review.jsonl'):
            # Baseline bytes preserved exactly as an export prefix.
            chunks = [(p / name).read_bytes() for p in source_dirs]
            require(all(c.endswith(b'\n') for c in chunks), 'Every source JSONL must end with newline')
            payload[name] = b''.join(chunks)
        expected = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
        if destination.exists():
            require(all((destination / n).exists() and digest(destination / n) == h for n, h in expected.items()), 'Export directory exists with different content; choose a fresh path')
            manifest = json_read(destination / 'manifest.json')
            require(manifest.get('artifacts') == expected and manifest.get('count') == self.output_count
                    and manifest.get('spec_sha256') == state['frozen_manifest_sha256']
                    and manifest.get('batch_checkpoints') == state['batches'],
                    'Existing export manifest differs from accepted checkpoint provenance')
            state['export'] = {'status': 'exported', 'path': str(destination), 'hashes': expected, 'exported_at': self.now()}
            self.save(state)
            return manifest
        temp = destination.with_name(destination.name + '.tmp')
        require(not temp.exists(), 'Incomplete export staging directory exists; inspect/remove it and rerun')
        temp.mkdir(parents=True)
        for name, data in payload.items():
            (temp / name).write_bytes(data)
        manifest = {'version': self.destination.name, 'count': self.output_count, 'artifacts': expected,
                    'spec_sha256': state['frozen_manifest_sha256'],
                    'baseline_hashes': json_read(self.frozen / 'manifest.json')['baseline'],
                    'batch_checkpoints': state['batches'],
                    'review_status': f'new_{self.output_count-self.baseline_count}_independent_model_reviewed_pending_human; baseline_preserved',
                    'tokenization_verified': False, 'training_executed': False}
        atomic(temp / 'manifest.json', manifest)
        (temp / 'README.md').write_text(f'{self.output_count}-row SFT export; baseline {self.baseline_count} preserved byte for byte as prefix.\nNew {self.output_count-self.baseline_count} passed structural checks and independent model audit; human review pending.\nNo held-out data opened, training run, tokenizer masks or learning claims.\nOnly prompt/completion belong in training; review.jsonl is external metadata.\n')
        temp.rename(destination)
        state['export'] = {'status': 'exported', 'path': str(destination), 'hashes': expected, 'exported_at': self.now()}
        self.save(state)
        return manifest

    def status(self):
        state = self.verify()
        for batch, record in state['batches'].items():
            if 'hashes' in record and not self.current(batch, record):
                record['effective_status'] = 'stale_files'
            else:
                record['effective_status'] = record['status']
                if record['status'] in ('audited', 'accepted'):
                    self.check_audit(batch, record)
        if 'export' in state:
            exported = state['export']
            exported['effective_status'] = 'exported' if all(
                (Path(exported['path']) / name).exists() and digest(Path(exported['path']) / name) == sha
                for name, sha in exported['hashes'].items()) else 'stale_files'
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=HERE.parent, help='stage1 root')
    parser.add_argument('--work-dir', type=Path, default=HERE, help='pipeline directory (for isolated test runs)')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('status')
    p = sub.add_parser('start')
    p.add_argument('--batch', required=True)
    p.add_argument('--generator-agent', required=True)
    p.add_argument('--correction', action='store_true')
    p.add_argument('--generator-model')
    p.add_argument('--generator-reasoning')
    for command in ('validate', 'accept'):
        p = sub.add_parser(command)
        p.add_argument('--batch', required=True)
    p = sub.add_parser('audit')
    p.add_argument('--batch', required=True)
    p.add_argument('--audit-file', type=Path, required=True)
    p = sub.add_parser('export')
    p.add_argument('--destination', type=Path)
    args = parser.parse_args()
    try:
        workflow = Workflow(args.root, args.work_dir)
        if args.command == 'start':
            result = workflow.start(args.batch, args.generator_agent, args.correction, args.generator_model, args.generator_reasoning)
        elif args.command in ('validate', 'accept'):
            result = getattr(workflow, args.command)(args.batch)
        elif args.command == 'audit':
            result = workflow.audit(args.batch, args.audit_file)
        elif args.command == 'export':
            result = workflow.export(args.destination)
        else:
            result = getattr(workflow, args.command)()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get('status') in ('validation_failed', 'audit_failed') else 0
    except (ValueError, KeyError, TypeError, OSError, AttributeError) as error:
        print(json.dumps({'error': str(error)}, indent=2), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
