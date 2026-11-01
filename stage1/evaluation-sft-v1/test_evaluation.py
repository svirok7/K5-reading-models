"""Offline integrity and comparison tests; all generated fixtures are synthetic."""
import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import compare_development as comparison
from prepare_reference import canonical, digest, file_hash, prepare, verify
import replay_development as replay

HERE = Path(__file__).resolve().parent


class EvaluationTests(unittest.TestCase):
    def test_snapshot_preserves_raw_body_and_never_mutates_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / 'source.sqlite3'
            row = {'id': 'synthetic-only', 'response': {'model': {'backend': 'qwen', 'adapter': None,
                'template': replay.TEMPLATE}}, 'condition': 'A', 'prompt': 'Synthetic test prompt',
                'rubric': 'Synthetic rubric', 'rubric_hash': digest('Synthetic rubric'),
                'rubric_version': 'test', 'messages': [{'role': 'user', 'content': 'Synthetic input'}]}
            body = json.dumps(row)
            with sqlite3.connect(database) as conn:
                conn.execute('CREATE TABLE records(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
                conn.execute('INSERT INTO records VALUES (?, ?)', (row['id'], body))
            before = file_hash(database)
            with redirect_stdout(io.StringIO()):
                prepare(database, root / 'reference')
            self.assertEqual(file_hash(database), before)
            source = json.loads((root / 'reference/source-bodies.jsonl').read_text())
            self.assertEqual(source['body'], body)
            self.assertEqual(verify(root / 'reference')['records'], 1)
            with self.assertRaises(ValueError):
                prepare(database, root / 'reference')

    def test_tampered_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'inputs.jsonl').write_text('original\n')
            (root / 'manifest.json').write_text(json.dumps({'files': {'inputs.jsonl': file_hash(root / 'inputs.jsonl')}}))
            verify(root)
            (root / 'inputs.jsonl').write_text('changed\n')
            with self.assertRaises(ValueError):
                verify(root)

    def test_frozen_reference_selections_require_no_model_import(self):
        args = argparse.Namespace(reference=HERE / 'baseline-reference', selection='current-only',
            adapter=None, run_record=None, device='mps', precision='float16', seed=42)
        cases, identity, record = replay.prepare(args)
        self.assertEqual(len(cases), 1)
        self.assertEqual(identity['revision'], replay.REVISION)
        self.assertIsNone(record)
        args.selection = 'all-no-thinking'
        cases, _, _ = replay.prepare(args)
        self.assertEqual(len(cases), 13)
        self.assertTrue(all(c['messages'][-1]['role'] == 'user' for c in cases))
        self.assertTrue(all('response' not in c and 'expected_behavior' not in c for c in cases))

    def fixture_runs(self, root, seed_mismatch=False):
        case = json.loads((HERE / 'baseline-reference/development-inputs.jsonl').read_text().splitlines()[0])
        for variant in ('base', 'sft'):
            folder = root / variant
            folder.mkdir()
            row = {**case, 'variant': variant, 'text': 'Synthetic ' + variant, 'status': 'completed',
                'truncated': False, 'latency_s': 1.0, 'seed': 43 if seed_mismatch and variant == 'sft' else 42,
                'rendered_input_sha256': 'synthetic-render', 'input_token_ids_sha256': 'synthetic-tokens'}
            (folder / 'responses.jsonl').write_text(canonical(row) + '\n')
            manifest = {'status': 'completed', 'case_count': 1, 'variant': variant,
                'reference_manifest_sha256': file_hash(HERE / 'baseline-reference/manifest.json'),
                'responses_sha256': file_hash(folder / 'responses.jsonl')}
            (folder / 'manifest.json').write_text(json.dumps(manifest))
        return argparse.Namespace(reference=HERE / 'baseline-reference', base=root / 'base',
            sft=root / 'sft', out=root / 'comparison')

    def test_mismatched_case_seed_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.fixture_runs(Path(directory), seed_mismatch=True)
            with self.assertRaisesRegex(ValueError, 'seed'):
                comparison.prepare(args)
            self.assertFalse(args.out.exists())

    def test_blind_ratings_preserve_unscored_and_show_both_transitions(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.fixture_runs(Path(directory))
            with redirect_stdout(io.StringIO()):
                comparison.prepare(args)
            rows = comparison.read_jsonl(args.out / 'review.jsonl')
            ratings = args.out / 'ratings.jsonl'
            ratings.write_text(''.join(canonical(r) + '\n' for r in rows))
            output = io.StringIO()
            with redirect_stdout(output):
                comparison.summarize(args.out, ratings)
            group = json.loads(output.getvalue())['groups'][0]
            self.assertEqual(group['decisions']['base'], {'unscored': 1})
            self.assertEqual(group['paired_reading'], {})
            key = json.loads((args.out / 'identity-key.json').read_text())
            for label, variant in key[rows[0]['case_id']].items():
                response = rows[0]['responses'][label]
                response['scores'] = {'word_types': 2 if variant == 'base' else 4, 'length': 4, 'rhythm': 4}
                response['meaningful'] = variant == 'base'
            ratings.write_text(''.join(canonical(r) + '\n' for r in rows))
            output = io.StringIO()
            with redirect_stdout(output):
                comparison.summarize(args.out, ratings)
            group = json.loads(output.getvalue())['groups'][0]
            self.assertEqual(group['paired_reading'], {'not_acceptable -> acceptable': 1})
            self.assertEqual(group['paired_meaningful'], {'True -> False': 1})


if __name__ == '__main__':
    unittest.main()
