import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('glimmer_train', Path(__file__).with_name('train.py'))
train = importlib.util.module_from_spec(spec)
spec.loader.exec_module(train)


class LaunchSafetyTests(unittest.TestCase):
    def test_heartbeat_transport_sends_only_keepalive_and_checks_http_status(self):
        from types import SimpleNamespace
        with patch.dict(train.os.environ, {'FIREWORKS_API_KEY': 'test-secret'}), patch.object(train.subprocess, 'run') as run:
            run.return_value = SimpleNamespace(returncode=0, stdout='{}\n200')
            self.assertTrue(train.send_heartbeat('ts-example'))
            args = run.call_args.args[0]
            self.assertNotIn('test-secret', ' '.join(args))
            self.assertIn('/session_heartbeat', run.call_args.kwargs['input'])
            self.assertEqual(train.json.loads(args[args.index('--data')+1]), {'session_id':'ts-example'})
            run.return_value = SimpleNamespace(returncode=0, stdout='{}\n503')
            self.assertFalse(train.send_heartbeat('ts-example'))
            with self.assertRaises(ValueError):
                train.send_heartbeat('invalid-session')

    def test_ipv4_resolver_handles_async_byte_hostnames(self):
        calls = []
        def original(*args):
            calls.append(args)
            return []
        with patch.object(train.socket, 'getaddrinfo', original):
            train.prefer_fireworks_ipv4()
            train.socket.getaddrinfo(b'api.fireworks.ai', 443)
            self.assertEqual(calls[-1][2], train.socket.AF_INET)
            train.socket.getaddrinfo('api.fireworks.ai', 443)
            self.assertEqual(calls[-1][2], train.socket.AF_INET)
            train.socket.getaddrinfo('example.com', 443)
            self.assertEqual(calls[-1][2], 0)

    def test_dedicated_and_sampling_changes_rejected(self):
        for key, changed in [('serverless', False), ('lora_rank', 0), ('epochs', 1),
                             ('generation_eval', True), ('eval_auto_carveout', True),
                             ('train_on_what', 'all_assistant_messages'),
                             ('evaluation_dataset', 'holdout.jsonl')]:
            cfg = train.config(); cfg[key] = changed
            with self.subTest(key=key), self.assertRaises(ValueError):
                train.validate_config(cfg)

    def test_valid_mask_then_stale_mask_revision_and_context_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory); ds = data / 'train.messages.jsonl'
            ds.write_text(('"unused"\n'))
            rows = [{'messages': [{'role': 'user', 'content': 'a'}, {'role': 'assistant', 'content': 'b'}]}] * 600
            ds.write_text(''.join(json.dumps(row) + '\n' for row in rows))
            (data / 'validation.json').write_text(json.dumps({'status':'passed','row_count':600}))
            mask = {'status':'passed','row_count':600,'train_on_what':'last_assistant_message',
                    'renderer':'muse_glimmer','context_loss_positions':0,'dropped_rows':0,
                    'truncated_rows':0,'dataset_sha256':train.sha256(ds),
                    'tokenizer_revision':train.config()['tokenizer_revision'],'max_rendered_tokens':100,
                    'cookbook_revision':train.PIN}
            snapshot = data / 'tokenizer'; snapshot.mkdir()
            (snapshot / 'tokenizer.json').write_text('{}')
            (snapshot / 'snapshot_manifest.json').write_text('{}')
            mask['tokenizer_snapshot_manifest_sha256'] = train.sha256(snapshot / 'snapshot_manifest.json')
            mask['tokenizer_files_sha256'] = {'tokenizer.json': train.sha256(snapshot / 'tokenizer.json')}
            proof_path = data / 'token_mask_proofs.jsonl'
            proof_path.write_text((json.dumps({'context_loss_positions':0,'datums':1}) + '\n') * 600)
            mask['proofs_sha256'] = train.sha256(proof_path)
            with patch.object(train, 'DATA', data), patch.object(train, 'DATASET', ds):
                for key, bad in [(None, None), ('dataset_sha256', 'stale'),
                                 ('tokenizer_revision', 'wrong'), ('context_loss_positions', 1),
                                 ('dropped_rows', 1), ('truncated_rows', 1),
                                 ('max_rendered_tokens', 999999)]:
                    current = copy.deepcopy(mask)
                    if key: current[key] = bad
                    (data / 'token_mask_validation.json').write_text(json.dumps(current))
                    with self.subTest(key=key):
                        if key:
                            with self.assertRaises(ValueError): train.data_gate(train.config())
                        else: train.data_gate(train.config())

    def test_promotion_cutoff_matches_documented_pacific_deadline(self):
        self.assertEqual(train.DEADLINE.isoformat(), '2026-12-01T08:00:00+00:00')

    def test_source_hashes_and_commit(self):
        train.source_gate()

    def test_plan_contains_no_credential(self):
        with patch.dict(train.os.environ, {'FIREWORKS_API_KEY':'secret-test-key'}):
            report = json.dumps(train.plan())
        self.assertNotIn('secret-test-key', report)
        self.assertIn('advertised_training_usd', report)
        self.assertEqual(train.plan()['inference_calls'], 0)


if __name__ == '__main__':
    unittest.main()
