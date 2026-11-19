"""Temporary mechanical UI fixtures, never evaluation cases; no network/model calls."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import ui_evaluation as e


class ExistingUIWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root/'ui.sqlite3'
        rubric = e.current_rubric()
        self.fixture = {'id':'fixture-1','messages':[{'role':'user','content':'Mechanical fixture'}],
                        'created_at':'fixture', 'condition':'B','prompt':e.engine.prompt_for('B'),
                        'rubric':rubric, 'rubric_hash':e.engine.digest(rubric),'rubric_version':'1.5',
                        'response':{'model':{'backend':'qwen','model':'fixture','adapter':'fixture'},
                                    'status':'completed','text':'Fixture','latency_s':1.0},
                        'evaluation':{'verdict':'not_acceptable','latency_s':2.0,
                                      'scores':{'word_types':2,'length':4,'rhythm':3}},
                        'manual':{'decision':'acceptable','reason':'Fixture'},'manual_history':[]}
        with sqlite3.connect(self.db) as c:
            c.execute('CREATE TABLE records(id TEXT PRIMARY KEY, body TEXT)')
            c.execute('INSERT INTO records VALUES (?,?)',('fixture-1',json.dumps(self.fixture)))
            # Archived body need not conform: excluded by SQL before Python loads it.
            c.execute('INSERT INTO records VALUES (?,?)',('archived',json.dumps({'archived_at':'fixture'})))

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        out = self.root/'export'
        e.export(self.db,out,backend='qwen',adapter='present',condition='B',rubric_version='1.5')
        return out

    def test_export_does_not_touch_database_or_include_archived(self):
        before = self.db.read_bytes()
        with patch('urllib.request.urlopen') as outbound:
            out = self.snapshot()
            outbound.assert_not_called()
        self.assertEqual(self.db.read_bytes(),before)
        loaded = e.load_export(out,e.sha(out/'manifest.json'))
        self.assertEqual([r['id'] for r in loaded],['fixture-1'])

    def test_ui_summary_keeps_manual_precedence_and_original_scores(self):
        summary = e.summarize([self.fixture])['groups'][0]
        self.assertEqual(summary['effective_decisions']['acceptable'],1)
        self.assertEqual(summary['manual_overrides'],1)
        self.assertEqual(summary['evaluator_score_means']['word_types'],2)
        self.assertEqual(summary['unique_exact_inputs'],1)

    def test_repeated_and_unpaired_histories_not_counted_as_unique_pairs(self):
        repeat = copy.deepcopy(self.fixture)
        repeat['id'] = 'fixture-2'
        other = copy.deepcopy(self.fixture)
        other['id'] = 'fixture-other'
        other['response']['model'] = {'backend':'qwen','model':'fixture','adapter':None}
        summary = e.summarize([self.fixture,repeat,other])
        self.assertEqual(len(summary['exact_input_overlap']),1)
        overlap = summary['exact_input_overlap'][0]
        self.assertEqual(overlap['exact_shared_inputs'],1)
        self.assertEqual(overlap['unambiguous_one_record_each'],0)

    def test_changed_snapshot_refused_and_export_never_overwrites(self):
        out = self.snapshot()
        manifest_sha = e.sha(out/'manifest.json')
        with self.assertRaises(FileExistsError):
            e.export(self.db,out)
        with (out/'records.jsonl').open('a') as handle:
            handle.write('{}\n')
        with self.assertRaisesRegex(ValueError,'Changed UI export'):
            e.load_export(out,manifest_sha)

    def test_replay_plan_uses_existing_messages_with_no_execution_capability(self):
        out = self.snapshot()
        plan = self.root/'plan.jsonl'
        with patch('urllib.request.urlopen') as outbound:
            self.assertEqual(e.replay_plan(out,e.sha(out/'manifest.json'),'fireworks',plan),1)
            outbound.assert_not_called()
        planned = e.rows(plan)
        self.assertEqual(planned[0]['request']['messages'],self.fixture['messages'])
        self.assertEqual(planned[0]['source_ids'],['fixture-1'])
        self.assertFalse(planned[0]['execution_permitted'])
        self.assertEqual(planned[0]['spend_limit_usd'],0)
        self.assertFalse(hasattr(e,'execute'))
        e.validate_plan(planned)
        planned[0]['request']['messages'][0]['content'] = 'Changed fixture'
        with self.assertRaisesRegex(ValueError,'binding mismatch'):
            e.validate_plan(planned)

    def test_old_rubric_cannot_be_silently_replayed_under_current_ui(self):
        self.fixture['rubric_hash'] = 'old-rubric'
        with sqlite3.connect(self.db) as c:
            c.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(self.fixture),'fixture-1'))
        out = self.snapshot()
        with self.assertRaisesRegex(ValueError,'Saved rubric differs'):
            e.replay_plan(out,e.sha(out/'manifest.json'),'fireworks',self.root/'plan.jsonl')


if __name__ == '__main__':
    unittest.main()
