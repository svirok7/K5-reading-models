import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('glimmer_worker', Path(__file__).with_name('worker.py'))
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

class Tokenizer:
    def encode(self, text, **kwargs):
        return [200022, 140680, 328, 76976, 200023]
    def decode(self, ids, **kwargs):
        return '<read>cat</read><|eot|>'

class WorkerSafetyTests(unittest.TestCase):
    def test_only_fixed_final_sampler_and_one_generation(self):
        requests = []
        def fake_post(path, body, request_id):
            requests.append((path, body))
            response = {'choices': [{'text': 'provider text', 'finish_reason': 'stop',
                'raw_output': {'completion_token_ids': [1, 2]}}],
                'usage': {'prompt_tokens': 5, 'completion_tokens': 2}, 'id': 'response-123'}
            return {'http_status': 200, 'curl_exit_code': 0, 'raw_response': response, 'response_headers': {}}
        with patch.object(worker, 'native', return_value=(Tokenizer(), None)), patch.object(worker, 'http_post', fake_post):
            result = worker.generate({'token_ids': Tokenizer().encode(''), 'model': 'wrong-model', 'max_tokens': 128})
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0], ('/api/v1/create_sampling_route', {'training_run': worker.RUN}))
        self.assertEqual(requests[1][1]['model'], worker.SAMPLER_MODEL)
        self.assertEqual(requests[1][1]['max_tokens'], 128)
        self.assertEqual(requests[1][1]['n'], 1)
        self.assertFalse(requests[1][1]['stream'])
        self.assertEqual(result['text'], '<read>cat</read>')
        self.assertEqual(result['usage']['output_tokens'], 2)
        self.assertEqual(result['raw_response']['id'], 'response-123')

    def test_caps_fail_before_network(self):
        with patch.object(worker, 'http_post') as network:
            for request in ({'token_ids': [1], 'max_tokens': 129}, {'token_ids': [1] * 8065}, {'token_ids': [-1]}):
                with self.assertRaises(ValueError):
                    worker.generate(request)
            network.assert_not_called()

    def test_failed_route_does_not_sample(self):
        with patch.object(worker, 'native', return_value=(Tokenizer(), None)), patch.object(worker, 'http_post',
            return_value={'http_status': 503, 'curl_exit_code': 0, 'raw_response': {'error': 'unavailable'}}) as network:
            result = worker.generate({'token_ids': Tokenizer().encode('')})
        network.assert_called_once()
        self.assertFalse(result['generation_attempted'])
        self.assertEqual(result['status'], 'error')

if __name__ == '__main__':
    unittest.main()
