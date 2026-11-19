import io
import json
import unittest
from unittest.mock import patch
from engine import FireworksEngine

class FireworksTests(unittest.TestCase):
    def generate(self, content='Hi.', reason='stop'):
        response = {'id':'test-id','model':'resolved', 'usage':{'total_tokens':12},
                    'choices':[{'message':{'content':content,'reasoning_content':'private reasoning'},
                                'finish_reason':reason}]}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as call:
            engine = FireworksEngine('deployment', 'test-secret', options={'temperature':0.7})
            result = engine.generate('profile', [{'role':'user','content':'Hi'}])
            request = call.call_args.args[0]
            body = json.loads(request.data)
            self.assertEqual(body['messages'], [{'role':'system','content':'profile'}, {'role':'user','content':'Hi'}])
            self.assertEqual(body['model'], 'deployment')
            self.assertNotIn('test-secret', json.dumps(engine.metadata))
            self.assertEqual(result['raw_response'], response)
            return result

    def test_visible_text_and_metadata(self):
        result = self.generate()
        self.assertEqual(result['text'], 'Hi.')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['usage']['total_tokens'], 12)
        self.assertEqual(result['resolved_model'], 'resolved')

    def test_length_and_empty_are_incomplete(self):
        self.assertTrue(self.generate(reason='length')['truncated'])
        self.assertEqual(self.generate(content='')['status'], 'incomplete')
        self.assertEqual(self.generate(content='   ')['status'], 'incomplete')

    def test_unknown_options_rejected(self):
        with self.assertRaises(ValueError):
            FireworksEngine('m', 'k', options={'seed':42})

if __name__ == '__main__': unittest.main()
