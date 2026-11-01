"""Mechanical fixtures only; these are NOT a development suite or new eval cases."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import evaluate as e


class EvaluationIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.reference = self.root/'frozen'
        self.reference.mkdir()
        self.cases = []
        for index, history in enumerate(('single_turn','multi_turn')):
            case_id = f'mechanical-fixture-{index}'
            messages = [{'role':'user','content':'Fixture'}]
            if index:
                messages = [{'role':'user','content':'Earlier fixture'},{'role':'assistant','content':'Old fixture'},*messages]
            case = dict(case_id=case_id,prompt='System fixture',messages=messages,history_kind=history)
            case['prompt_hash'] = e.hashlib.sha256(case['prompt'].encode()).hexdigest()
            case['input_hash'] = e.digest({k:case[k] for k in ('prompt','messages')})
            case['seed'] = (42+int(e.hashlib.sha256(case_id.encode()).hexdigest()[:8],16)) % 2**32
            self.cases.append(case)
        e.jsonl(self.reference/'cases.jsonl',self.cases)
        self.seal()

    def tearDown(self):
        self.temp.cleanup()

    def seal(self):
        e.write(self.reference/'manifest.json',dict(case_count=2,files={'cases.jsonl':e.sha(self.reference/'cases.jsonl')}))
        self.reference_sha = e.sha(self.reference/'manifest.json')

    def run_fixture(self,label, **overrides):
        path = self.root/label
        path.mkdir()
        data = [dict(case_id=c['case_id'],input_hash=c['input_hash'],seed=c['seed'],text='Raw fixture',history_kind=c['history_kind'],status='completed') for c in self.cases]
        e.jsonl(path/'responses.jsonl',data)
        identity = dict(status='completed',frozen_manifest_sha256=self.reference_sha,responses_sha256=e.sha(path/'responses.jsonl'),adapter_record_sha256=label,base_model=e.MODEL,revision=e.REVISION,template=e.TEMPLATE,enable_thinking=False,generation=e.GENERATION,precision='float16',hardware='Tesla T4',cuda='fixture',python='fixture',packages={},seed_offset=0,model_tokenizer_artifacts_sha256='a'*64,actual_parameter_dtypes={'torch.float16':1},attention_implementation='sdpa')
        identity.update(overrides)
        e.write(path/'manifest.json',identity)
        return str(path)

    def blind_fixture(self):
        out = self.root/'blind'
        e.blind(self.reference,self.reference_sha,{'current':self.run_fixture('current'),'same300-epoch1':self.run_fixture('candidate')},out)
        return out

    def rating_fixture(self,out):
        key = json.loads((out/'identity-key.json').read_text())
        return [dict(review_id=review_id,word_types=3,length=4,rhythm=4,meaningful_relevant=True,truthful=True,safe=True,repetition_or_correction_failure=False,serious_safety_failure=False,serious_identity_failure=False,unsupported_words=[],rationale='Mechanical fixture') for review_id in key]

    def test_frozen_targets_and_notes_rejected_even_if_resealed(self):
        self.cases[0]['expected_behavior'] = 'Must never reach generation'
        (self.reference/'cases.jsonl').unlink()
        e.jsonl(self.reference/'cases.jsonl',self.cases)
        self.seal()
        with self.assertRaisesRegex(ValueError,'Targets/notes'):
            e.frozen(self.reference,self.reference_sha)

    def test_immutable_manifest_and_messages(self):
        self.assertEqual(len(e.frozen(self.reference,self.reference_sha)),2)
        self.reference.joinpath('cases.jsonl').write_text('changed')
        with self.assertRaisesRegex(ValueError,'Changed frozen'):
            e.frozen(self.reference,self.reference_sha)

    def test_blind_inputs_exclude_variant_and_tokens(self):
        out = self.blind_fixture()
        reviews = e.rows(out/'review.jsonl')
        self.assertEqual(len(reviews),4)
        self.assertTrue(all(set(r)=={'review_id','messages','history_kind','text'} for r in reviews))

    def test_blind_rejects_different_precision_or_seed(self):
        runs = {'current':self.run_fixture('current'),'candidate':self.run_fixture('candidate',precision='bfloat16')}
        with self.assertRaisesRegex(ValueError,'Inference groups differ'):
            e.blind(self.reference,self.reference_sha,runs,self.root/'blind')

    def test_joint_and_new_serious_failure_by_type(self):
        out = self.blind_fixture()
        ratings = self.rating_fixture(out)
        key = json.loads((out/'identity-key.json').read_text())
        for rating in ratings:
            if key[rating['review_id']]['case_id'] == self.cases[0]['case_id']:
                if key[rating['review_id']]['variant'] == 'current':
                    rating.update(serious_identity_failure=True,truthful=False)
                else:
                    rating.update(serious_safety_failure=True,safe=False)
        path = self.root/'ratings.jsonl'
        e.jsonl(path,ratings)
        result = e.summarize(out,path,'current',self.root/'summary.json')
        self.assertEqual(result['same300-epoch1']['joint_successes'],1)
        self.assertEqual(result['same300-epoch1']['new_serious_failures'],[self.cases[0]['case_id']])
        self.assertEqual(result['same300-epoch1']['groups']['multi_turn']['joint_successes'],1)
        self.assertFalse(result['same300-epoch1']['qualifies_for_repeat_seeds'])

    def test_duplicate_or_incomplete_review_refused(self):
        out = self.blind_fixture()
        ratings = self.rating_fixture(out)
        ratings[-1] = copy.deepcopy(ratings[0])
        path = self.root/'ratings.jsonl'
        e.jsonl(path,ratings)
        with self.assertRaisesRegex(ValueError,'every response exactly once'):
            e.summarize(out,path,'current',self.root/'summary.json')

    def test_unsupported_word_cannot_score_reading_pass(self):
        out = self.blind_fixture()
        ratings = self.rating_fixture(out)
        ratings[0]['unsupported_words'] = ['fixture']
        path = self.root/'ratings.jsonl'
        e.jsonl(path,ratings)
        with self.assertRaisesRegex(ValueError,'Unsupported word'):
            e.summarize(out,path,'current',self.root/'summary.json')


if __name__ == '__main__':
    unittest.main()
