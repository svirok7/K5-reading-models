"""Focused content/mask-contract regressions; no network or model calls."""
import copy
import tempfile
import unittest
from pathlib import Path
import convert_dataset as c

class DatasetTests(unittest.TestCase):
    def test_frozen_source_and_all_exported_rows(self):
        result = c.validate_export()
        self.assertEqual(result['row_count'], 600)
        self.assertTrue(result['all_history_messages_preserved'])
        self.assertEqual(result['historical_assistant_turns_context_only_planned'], 601)
        self.assertEqual(result['rows_with_annotated_history_flaws'], 143)

    def test_history_defects_are_preserved_and_excluded_by_plan(self):
        rows = c.jsonl(c.SOURCE / 'sft.jsonl')
        reviews = c.jsonl(c.SOURCE / 'review.jsonl')
        plans = c.jsonl(c.HERE / 'row_identity_and_mask_plan.jsonl')
        checked = 0
        for row, review, plan in zip(rows, reviews, plans):
            if review.get('flawed_history_indices'):
                converted = c.convert_row(row)['messages']
                self.assertEqual(converted[:-1], row['prompt'])
                self.assertEqual(plan['message_loss_plan'][:-1], [0] * len(row['prompt']))
                self.assertEqual(plan['message_loss_plan'][-1], 1)
                checked += 1
        self.assertEqual(checked, 143)

    def test_extra_completion_and_weight_fields_fail_closed(self):
        row = c.jsonl(c.SOURCE / 'sft.jsonl')[0]
        extra = copy.deepcopy(row)
        extra['completion'].append({'role': 'assistant', 'content': 'extra'})
        with self.assertRaises(ValueError): c.convert_row(extra)
        weighted = copy.deepcopy(row)
        weighted['prompt'][0]['weight'] = 0
        with self.assertRaises(ValueError): c.convert_row(weighted)

    def test_export_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            c.export(output=Path(temp))
            for name in ('train.messages.jsonl', 'row_identity_and_mask_plan.jsonl', 'validation.json'):
                self.assertEqual((Path(temp) / name).read_bytes(), (c.HERE / name).read_bytes())

    def test_changed_target_or_mask_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            c.export(output=temp)
            exported = c.jsonl(temp / 'train.messages.jsonl')
            exported[0]['messages'][-1]['content'] += ' changed'
            (temp / 'train.messages.jsonl').write_bytes(b''.join(c.canonical(r) + b'\n' for r in exported))
            with self.assertRaisesRegex(ValueError, 'Content identity'): c.validate_export(output=temp)
            c.export(output=temp)
            plans = c.jsonl(temp / 'row_identity_and_mask_plan.jsonl')
            plans[0]['message_loss_plan'][0] = 1
            (temp / 'row_identity_and_mask_plan.jsonl').write_bytes(b''.join(c.canonical(r) + b'\n' for r in plans))
            with self.assertRaisesRegex(ValueError, 'Invalid identity/mask'): c.validate_export(output=temp)

if __name__ == '__main__': unittest.main()
