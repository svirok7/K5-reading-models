"""Selection algorithm fixtures, not new model evaluation cases."""
import copy
import unittest
from choose_checkpoint import choose


class Selection(unittest.TestCase):
    def fixture(self):
        result = {'joint_successes':9,'joint_gain_percentage_points':25,'new_serious_failures':[]}
        summary = dict(reference='current',seed_offset=0,independent_cases=4,frozen_manifest_sha256='frozen',comparison_group={'precision':'float16'},candidate_record_hashes={'current':'base','early':'e1','late':'e2'},results={'current':dict(result,joint_successes=2,joint_gain_percentage_points=0),'early':dict(result,joint_successes=3),'late':dict(result,joint_successes=3)})
        metadata = {'early':{'epoch':1,'updates':38},'late':{'epoch':2,'updates':76}}
        return summary,metadata

    def test_earlier_checkpoint_tie_and_repeats_required(self):
        summary,metadata=self.fixture()
        result=choose(summary,metadata)
        self.assertEqual(result['selected'],'early')
        self.assertEqual(result['recommendation'],'pending_repeat_seeds')

    def repeats(self,summary):
        repeats=[]
        for offset in (1000003,2000003):
            repeat=copy.deepcopy(summary)
            repeat['seed_offset']=offset
            repeat['results'].pop('late')
            repeat['candidate_record_hashes'].pop('late')
            repeats.append(repeat)
        return repeats

    def test_adoption_requires_both_paired_repeats(self):
        summary,metadata=self.fixture()
        repeats=self.repeats(summary)
        self.assertEqual(choose(summary,metadata,repeats)['recommendation'],'recommend_for_user_adoption')
        repeats[1]['results']['early']['joint_gain_percentage_points']=0
        self.assertEqual(choose(summary,metadata,repeats)['recommendation'],'retain_current')

    def test_repeat_cannot_switch_checkpoint_or_cases(self):
        summary,metadata=self.fixture()
        repeats=self.repeats(summary)
        repeats[1]['candidate_record_hashes']['early']='another adapter'
        with self.assertRaisesRegex(ValueError,'changed frozen inputs or selected checkpoint'):
            choose(summary,metadata,repeats)

    def test_new_serious_failure_cannot_be_compensated(self):
        summary,metadata=self.fixture()
        summary['results']['early']['new_serious_failures']=['case']
        self.assertEqual(choose(summary,metadata)['recommendation'],'retain_current')


if __name__=='__main__': unittest.main()
