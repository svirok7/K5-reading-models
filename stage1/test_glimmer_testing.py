import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import glimmer_testing as glimmer
import server
from testing_budget import BudgetLedger


class GlimmerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.budget = BudgetLedger(Path(self.directory.name) / 'budget.sqlite3')

    def test_reserves_before_generation_and_normalizes_ui_result(self):
        engine = glimmer.GlimmerTestingEngine('fixture')
        def worker(body):
            if body['mode'] == 'prepare':
                self.assertEqual(self.budget.status()['reservation_count'], 0)
                return {'token_ids':[1,2,3]}
            self.assertEqual(self.budget.status()['reservation_count'], 1)
            return {'status':'ok','text':'Hi, Sam.','finish_reason':'stop','truncated':False,
                    'usage_source':'provider','usage':{'input_tokens':3,'output_tokens':4}}
        with patch.object(glimmer,'ledger',return_value=self.budget), patch.object(engine,'_worker',side_effect=worker):
            result = engine.generate('Profile', [{'role':'user','content':'Hi'}])
        self.assertEqual(result['status'],'completed')
        self.assertEqual(result['diagnostics']['words'],2)
        self.assertEqual(self.budget.status()['reserved_usd'],'0.000000000')

    def test_failed_request_keeps_full_reservation(self):
        engine = glimmer.GlimmerTestingEngine('fixture')
        with patch.object(glimmer,'ledger',return_value=self.budget), patch.object(engine,'_worker',side_effect=[{'token_ids':[1,2,3]},RuntimeError('failed')]):
            with self.assertRaises(RuntimeError): engine.generate('p',[{'role':'user','content':'Hi'}])
        self.assertGreater(float(self.budget.status()['reserved_usd']),0)
        self.assertEqual(self.budget.status()['failed_count'],1)

    def test_successful_reply_survives_accounting_error(self):
        engine=glimmer.GlimmerTestingEngine('fixture')
        reply={'status':'ok','text':'A cat can hop.','finish_reason':'stop',
               'usage_source':'provider','usage':{'input_tokens':3,'output_tokens':5}}
        with patch.object(glimmer,'ledger',return_value=self.budget),patch.object(engine,'_worker',side_effect=[{'token_ids':[1,2,3]},reply]),patch.object(self.budget,'settle',side_effect=RuntimeError('accounting unavailable')):
            result=engine.generate('p',[{'role':'user','content':'Hi'}])
        self.assertEqual(result['text'],'A cat can hop.')
        self.assertIn('budget_warning',result)
        self.assertGreater(float(self.budget.status()['reserved_usd']),0)

    def test_exhausted_budget_prevents_generation(self):
        for n in range(7):
            self.budget.reserve('judge',100000,3000,model='gpt-6.1-sol',request_id=f'fill-{n}')
        self.budget.reserve('judge',50000,3000,model='gpt-6.1-sol',request_id='fill-last')
        with patch.object(glimmer,'ledger',return_value=self.budget):
            engine=glimmer.GlimmerTestingEngine('fixture')
            worker=Mock(return_value={'token_ids':[1]*8064})
            with patch.object(engine,'_worker',worker):
                with self.assertRaises(RuntimeError):engine.generate('p',[{'role':'user','content':'Hi'}])
            self.assertEqual(worker.call_count,1)

    def request(self, body):
        handler = object.__new__(server.Handler)
        handler.path='/api/evaluate'
        raw=json.dumps(body).encode()
        handler.headers={'Host':f'127.0.0.1:{server.PORT}','Origin':f'http://127.0.0.1:{server.PORT}',
                         'Content-Type':'application/json','Content-Length':str(len(raw))}
        handler.rfile=io.BytesIO(raw);handler.send=Mock()
        handler.do_POST()
        return handler.send.call_args.args

    def test_budget_flag_cannot_enable_judging_another_model(self):
        row={'id':'fixture','response':{'model':{'backend':'qwen','model':'fixture'}}}
        with patch.object(server,'ZERO_COST_MODE',True),patch.object(server.records,'get',return_value=row),patch.object(server.evaluator,'evaluate') as evaluate:
            status,_=self.request({'id':'fixture','model':'glimmer_sft'})
        self.assertEqual(status,403);evaluate.assert_not_called()

    def test_budgeted_glimmer_uses_unchanged_judge_with_budget_wrapper(self):
        row={'id':'fixture','response':{'model':{'backend':'fireworks_sampler','model':glimmer.MODEL}},'evaluation':None}
        with patch.object(server,'ZERO_COST_MODE',True),patch.object(server.records,'get',return_value=row),patch.object(server.records,'update',return_value=row),patch.object(server.evaluator,'evaluate',return_value={}) as evaluate:
            status,_=self.request({'id':'fixture','model':'glimmer_sft'})
        self.assertEqual(status,200)
        self.assertIs(evaluate.call_args.kwargs['engine_class'],glimmer.BudgetedReadingJudge)

    def test_judge_reserves_before_outbound_and_settles_reported_usage(self):
        def generate(*args):
            self.assertEqual(self.budget.status()['reservation_count'],1)
            return {'usage':{'input_tokens':20,'output_tokens':30},'text':'{}'}
        judge=glimmer.BudgetedReadingJudge('gpt-6.1-sol','fixture',max_tokens=3000)
        self.assertEqual(judge.options['service_tier'],'default')
        with patch.object(glimmer,'ledger',return_value=self.budget),patch.object(glimmer.OpenAIEngine,'generate',side_effect=generate):
            judge.generate('Rubric',[{'role':'user','content':'Candidate'}])
        self.assertEqual(self.budget.status()['reserved_usd'],'0.000000000')


if __name__=='__main__':unittest.main()
