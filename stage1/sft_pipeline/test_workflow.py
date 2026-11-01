"""Synthetic structural fixtures only; never loads project benchmark or real rows."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from workflow import CHECKS, HERE, Workflow, atomic, digest, rows


def jsonl(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(v) + '\n' for v in values))


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'stage1'
        self.work = self.root / 'sft_pipeline'
        self.work.mkdir(parents=True)
        for name in ('spec.json', 'GENERATOR.md', 'AUDITOR.md'):
            shutil.copyfile(HERE / name, self.work / name)
        (self.root / 'READER_PROFILE.txt').write_text('fixture profile')
        (self.root / 'RUBRIC.md').write_text('fixture rubric')
        (self.root / 'data').mkdir()
        atomic(self.root / 'data/dolch-through-grade1.json', {'groups': {'fixture': ['a', 'can']}})
        base = self.root / 'datasets/sft-100-v1'
        jsonl(base / 'sft.jsonl', [{'prompt': [{'role': 'system', 'content': 'fixture system'}, {'role': 'user', 'content': 'hi'}], 'completion': [{'role': 'assistant', 'content': f'baseline {n}'}]} for n in range(100)])
        jsonl(base / 'review.jsonl', [{'id': f'pilot-{n+1:03}'} for n in range(100)])
        self.flow = Workflow(self.root, self.work)
        self.flow.init()

    def tearDown(self):
        self.temp.cleanup()

    def batch(self, batch='004'):
        first = self.flow.id_number(self.flow.batch_config[batch]['first_id'])
        sft, review = [], []
        for i in range(50):
            final = ' '.join(['hi'] * (1 if i < 20 else 6 if i < 40 else 16))
            context = ([{'role': 'user', 'content': 'hi'}, {'role': 'assistant', 'content': 'A cat.'}] if i < 16 else []) + [{'role': 'user', 'content': final}]
            target = f'A cat can hop. {first+i}'
            sft.append({'prompt': [{'role': 'system', 'content': 'fixture system'}] + context,
                        'completion': [{'role': 'assistant', 'content': target}]})
            review.append({'id': f'pilot-{first+i:03}', 'context_messages': context,
                           'target_response': target, 'requires_history': i < 16,
                           'input_length_bucket': 'short' if i < 20 else 'medium' if i < 40 else 'long',
                           'category': 'fixture', 'scenario_family': f'fixture-{i}',
                           'word_choice_reasoning': 'Fixture evidence; not a semantic approval.',
                           'review_checks': {'unresolved_words': [], 'human_approved': False},
                           'lexical_evidence': {'a': 'Exact Dolch entry', 'cat': 'short a', 'can': 'Exact Dolch entry', 'hop': 'short o'}})
        jsonl(self.flow.path(batch) / 'sft.jsonl', sft)
        jsonl(self.flow.path(batch) / 'review.jsonl', review)
        generator = self.flow.config.get('generator', {})
        self.flow.start(batch, 'generator', generator_model=generator.get('model'), generator_reasoning=generator.get('reasoning_effort'))
        self.assertEqual(self.flow.validate(batch)['status'], 'validated')

    def report(self, batch='004'):
        return {'batch': batch, 'spec_sha256': digest(self.flow.work / 'frozen/manifest.json'),
                **self.flow.hashes(batch),
                'auditor': {'agent_id': 'auditor', 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high'},
                'examples': [{'id': r['id'], 'verdict': 'pass', 'checks': dict.fromkeys(CHECKS, True), 'findings': []}
                             for r in rows(self.flow.path(batch) / 'review.jsonl')]}

    def audit(self, report, batch='004'):
        path = self.root / f'audit-{batch}.json'
        atomic(path, report)
        return self.flow.audit(batch, path)

    def accepted(self, batch='004'):
        self.batch(batch)
        self.audit(self.report(batch), batch)
        self.flow.accept(batch)

    def test_sequential_accept_resume_export_preserves_baseline(self):
        with self.assertRaisesRegex(ValueError, '004 must be accepted'):
            self.flow.start('005', 'generator')
        self.accepted()
        # Fresh process equivalent: derive state from stored files, no re-generation.
        recovered = Workflow(self.root, self.work)
        self.assertEqual(recovered.init()['batches']['004']['effective_status'], 'accepted')
        self.assertEqual(recovered.start('004', 'generator')['batches']['004']['status'], 'accepted')
        self.accepted('005')
        baseline = (self.root / 'datasets/sft-100-v1/sft.jsonl').read_bytes()
        manifest = self.flow.export()
        exported = self.root / 'datasets/sft-200-v1'
        self.assertEqual(len(rows(exported / 'sft.jsonl')), 200)
        self.assertTrue((exported / 'sft.jsonl').read_bytes().startswith(baseline))
        self.assertEqual(self.flow.export()['artifacts'], manifest['artifacts'])

    def test_stale_audit_and_acceptance_rejected_after_disk_edit(self):
        self.batch()
        report = self.report()
        path = self.flow.path('004') / 'review.jsonl'
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'Stale validation'):
            self.audit(report)
        self.assertEqual(self.flow.status()['batches']['004']['effective_status'], 'stale_files')
        self.flow.start('004', 'generator', True)
        self.flow.validate('004')
        with self.assertRaisesRegex(ValueError, 'Stale audit review_sha256'):
            self.audit(report)
        self.audit(self.report())
        self.flow.accept('004')
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.flow.accept('004')
        with self.assertRaisesRegex(ValueError, '004 must be accepted'):
            self.flow.start('005', 'generator')

    def test_findings_block_even_pass_verdict_and_low_severity(self):
        self.batch()
        report = self.report()
        report['examples'][0]['findings'] = [{'id': 'F1', 'severity': 'low', 'status': 'open', 'detail': 'Needs clarification'}]
        self.assertEqual(self.audit(report)['status'], 'audit_failed')
        with self.assertRaisesRegex(ValueError, 'passing independent audit'):
            self.flow.accept('004')
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            self.audit(self.report())

    def test_auditor_identity_and_complete_coverage_required(self):
        self.batch()
        for mutate in (
            lambda r: r['auditor'].update(agent_id='generator'),
            lambda r: r['auditor'].update(model='other'),
            lambda r: r['auditor'].update(reasoning_effort='low'),
            lambda r: r['examples'].pop(),
            lambda r: r['examples'][0]['checks'].pop('word_eligibility'),
        ):
            report = self.report()
            mutate(report)
            with self.assertRaises(ValueError):
                self.audit(report)
        self.audit(self.report())
        audit_file = self.work / 'checkpoints/004/round-0-audit.json'
        audit_file.write_text(audit_file.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'Stored audit changed'):
            self.flow.accept('004')

    def test_three_corrections_max_and_round_snapshots(self):
        self.batch()
        for round_number in range(4):
            report = self.report()
            report['examples'][0]['verdict'] = 'fail'
            self.audit(report)
            self.assertTrue((self.work / f'checkpoints/004/round-{round_number}-audit.json').exists())
            if round_number < 3:
                self.flow.start('004', 'generator', True)
                self.flow.validate('004')
        with self.assertRaisesRegex(ValueError, 'three correction rounds'):
            self.flow.start('004', 'generator', True)

    def test_baseline_and_frozen_changes_cannot_refreeze(self):
        path = self.root / 'datasets/sft-100-v1/review.jsonl'
        original = path.read_text()
        path.write_text(original + '\n')
        with self.assertRaisesRegex(ValueError, 'Frozen baseline changed'):
            self.flow.init()
        path.write_text(original)
        (self.work / 'frozen/spec.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Frozen specification changed'):
            self.flow.status()

    def test_sentence_limit_alignment_and_bad_dolch_evidence(self):
        self.batch()
        path = self.flow.path('004') / 'review.jsonl'
        reviews = rows(path)
        reviews[0]['lexical_evidence']['hop'] = 'Exact Dolch entry'
        reviews[1]['target_response'] = 'Mismatch'
        jsonl(path, reviews)
        self.flow.start('004', 'generator', True)
        result = self.flow.validate('004')
        self.assertEqual(result['status'], 'validation_failed')
        self.assertTrue(any('false exact-Dolch' in e for e in result['errors']))
        self.assertTrue(any('alignment mismatch' in e for e in result['errors']))

    def test_malformed_message_schema_produces_validation_error(self):
        self.batch()
        path = self.flow.path('004') / 'sft.jsonl'
        data = rows(path)
        data[0]['prompt'] = 'broken'
        jsonl(path, data)
        self.flow.start('004', 'generator', True)
        result = self.flow.validate('004')
        self.assertEqual(result['status'], 'validation_failed')
        self.assertTrue(any('message objects' in e for e in result['errors']))

    def test_configurable_200_to_300_run_preserves_earlier_workflow(self):
        original_state = self.flow.state_path.read_bytes()
        old_frozen = (self.work / 'frozen/manifest.json').read_bytes()
        work300 = self.root / 'sft_pipeline_300'
        work300.mkdir()
        for name in ('spec.json', 'GENERATOR.md', 'AUDITOR.md'):
            shutil.copyfile(HERE.with_name('sft_pipeline_300') / name, work300 / name)
        base = self.root / 'datasets/sft-200-v1'
        original = rows(self.root / 'datasets/sft-100-v1/sft.jsonl')
        extra = copy.deepcopy(original)
        for i, row in enumerate(extra):
            row['completion'][0]['content'] = f'baseline {i+100}'
        jsonl(base / 'sft.jsonl', original + extra)
        jsonl(base / 'review.jsonl', [{'id': f'pilot-{i+1:03}'} for i in range(200)])
        self.flow = Workflow(self.root, work300)
        self.flow.init()
        self.assertEqual(self.flow.batches, ('006', '007'))
        with self.assertRaisesRegex(ValueError, 'Generator must attest'):
            self.flow.start('006', 'generator')
        with self.assertRaisesRegex(ValueError, '006 must be accepted'):
            self.flow.start('007', 'generator', generator_model='gpt-6.1-sol', generator_reasoning='high')
        self.accepted('006')
        self.accepted('007')
        result = self.flow.export()
        self.assertEqual(result['version'], 'sft-300-v1')
        self.assertEqual(result['count'], 300)
        self.assertEqual(len(rows(self.root / 'datasets/sft-300-v1/sft.jsonl')), 300)
        self.assertTrue((self.root / 'datasets/sft-300-v1/sft.jsonl').read_bytes().startswith((base / 'sft.jsonl').read_bytes()))
        self.assertEqual((self.work / 'state.json').read_bytes(), original_state)
        self.assertEqual((self.work / 'frozen/manifest.json').read_bytes(), old_frozen)


if __name__ == '__main__':
    unittest.main()
