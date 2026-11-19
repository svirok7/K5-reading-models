"""The $0 default blocks before provider constructors or judge calls. No network."""
import io
import json
import unittest
from unittest.mock import Mock, patch
import server


class ZeroCostTests(unittest.TestCase):
    def request(self, route, body):
        handler = object.__new__(server.Handler)
        handler.path = route
        raw = json.dumps(body).encode()
        origin = f'http://127.0.0.1:{server.PORT}'
        handler.headers = {'Host':f'127.0.0.1:{server.PORT}', 'Origin':origin,
                           'Content-Type':'application/json', 'Content-Length':str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        handler.send = Mock()
        handler.do_POST()
        return handler.send.call_args.args

    def test_each_paid_backend_is_blocked_before_construction(self):
        with patch.object(server, 'ZERO_COST_MODE', True), \
             patch.object(server, 'OpenAIEngine') as openai, \
             patch.object(server, 'ClaudeEngine') as claude, \
             patch.object(server, 'FireworksEngine') as fireworks, \
             patch('urllib.request.urlopen') as network:
            for backend in ('openai','claude','fireworks'):
                with patch.object(server, 'registry', return_value={'fixture':{'backend':backend}}):
                    status, value = self.request('/api/chat', {'model':'fixture','condition':'B','messages':[{'role':'user','content':'Fixture'}]})
                self.assertEqual(status,403)
                self.assertIn('$0 mode', value['error'])
            for mock in (openai,claude,fireworks,network):
                mock.assert_not_called()

    def test_evaluator_is_blocked_before_record_access_or_outbound_call(self):
        with patch.object(server, 'ZERO_COST_MODE', True), \
             patch.object(server.records, 'get') as get, \
             patch.object(server.evaluator, 'evaluate') as evaluate, \
             patch('urllib.request.urlopen') as network:
            status, value = self.request('/api/evaluate', {'id':'fixture'})
            self.assertEqual(status,403)
            self.assertIn('manually', value['error'])
            for mock in (get,evaluate,network):
                mock.assert_not_called()

    def test_local_generation_and_manual_decisions_still_work(self):
        local = Mock()
        local.metadata = {'backend':'qwen','model':'fixture'}
        local.generate.return_value = {'text':'Fixture','status':'completed'}
        with patch.object(server, 'ZERO_COST_MODE', True), \
             patch.object(server, 'registry', return_value={'fixture':{'backend':'qwen'}}), \
             patch.dict(server.STATE, {'engine_id':None,'engine':None}), \
             patch.object(server, 'QwenEngine', return_value=local), \
             patch.object(server.records, 'create', return_value={'id':'saved'}), \
             patch.object(server.records, 'set_manual', return_value={'id':'saved','effective_decision':'acceptable'}) as manual, \
             patch('urllib.request.urlopen') as network:
            status, value = self.request('/api/chat', {'model':'fixture','condition':'B','messages':[{'role':'user','content':'Fixture'}]})
            self.assertEqual(status,200)
            self.assertEqual(value['record']['id'],'saved')
            status, value = self.request('/api/manual', {'id':'saved','decision':'acceptable','reason':'Fixture'})
            self.assertEqual(status,200)
            manual.assert_called_once_with('saved','acceptable','Fixture')
            network.assert_not_called()

    def test_future_explicit_opt_in_path_preserves_evaluator(self):
        with patch.object(server, 'ZERO_COST_MODE', False), \
             patch.object(server.records, 'get', return_value={'id':'fixture','evaluation':None}), \
             patch.object(server.records, 'update', return_value={'id':'fixture','evaluation':{'verdict':'acceptable'}}), \
             patch.object(server.evaluator, 'evaluate', return_value={'verdict':'acceptable'}) as evaluate:
            status, _ = self.request('/api/evaluate', {'id':'fixture'})
            self.assertEqual(status,200)
            evaluate.assert_called_once()


if __name__ == '__main__':
    unittest.main()
