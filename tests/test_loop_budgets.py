import unittest
from aikya.core.budgets import remaining
from aikya.core.checkpoints import account,create
from pathlib import Path

class BudgetTests(unittest.TestCase):
    def setUp(self):self.ledger=create(Path.cwd(),{})
    def result(self,ident='r1',turns=3):
        return {'id':ident,'session_id':'s','cost_usd':0.01,'num_turns':turns,
                'model_usage':{'synthetic':{k:10 for k in ('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens')}}}
    def test_review_shares_total_turn_budget(self):
        account(self.ledger,self.result())
        self.assertEqual(remaining({'max_turns':5,'max_total_turns':4},self.ledger)['max_turns'],1)
    def test_duplicate_result_is_idempotent(self):
        account(self.ledger,self.result());account(self.ledger,self.result())
        self.assertEqual(remaining({'max_turns':5,'max_total_turns':4},self.ledger)['max_turns'],1)
    def test_unknown_usage_cannot_satisfy_enabled_budget(self):
        account(self.ledger,{'id':'r','session_id':'s','cost_usd':0.01})
        self.assertEqual(remaining({'max_turns':5,'max_recorded_tokens':100},self.ledger)['reason'],'token_usage_unavailable')
    def test_total_tokens_include_cache_and_limit_stops_next_query(self):
        account(self.ledger,self.result())
        self.assertEqual(remaining({'max_turns':5,'max_recorded_tokens':40},self.ledger)['reason'],'token_limit')

if __name__=='__main__':unittest.main()
