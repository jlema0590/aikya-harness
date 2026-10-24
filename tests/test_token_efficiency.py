import json
import tempfile
import unittest
from pathlib import Path

from aikya.routing.policy import validated, resolved_agent_model
from aikya.routing.usage import summarize, estimate_cost, estimate_haiku_55_request

class PolicyTests(unittest.TestCase):
    def test_v591_backwards_compatibility(self):
        policy = validated(None)
        self.assertEqual(resolved_agent_model("planner", policy), "opus")
        self.assertEqual(resolved_agent_model("java-developer", policy), "inherit")
        self.assertFalse(policy["auxiliary_enabled"])

    def test_no_auxiliary_without_approval(self):
        with self.assertRaises(ValueError):
            validated({"auxiliary_enabled": True, "auxiliary_model": "haiku"})

    def test_auxiliary_opt_in(self):
        p = validated({"schema_version": 1, "auxiliary_enabled": True, "user_approved": True,
                       "auxiliary_model": "haiku"})
        self.assertEqual(resolved_agent_model("log-summarizer", p), "haiku")
        self.assertEqual(resolved_agent_model("security-reviewer", p), "inherit")

    def test_missing_prices_not_reported_as_zero_bill(self):
        data = {"models": {"sonnet": {"input_tokens": 1000000}}}
        r = estimate_cost(data, {"models": {}})
        self.assertIsNone(r["total_estimated"])
        self.assertEqual(r["models_missing_prices"], ["sonnet"])

    def test_user_supplied_prices(self):
        data = {"models": {"sonnet": {"input_tokens": 1000000,
                                       "output_tokens": 100000}}}
        rates = {"models": {"sonnet": {"input": 2, "output": 10,
                                        "cache_creation": 2.5, "cache_read": .2}}}
        self.assertEqual(estimate_cost(data, rates)["total_estimated"], 3.0)

    def test_invalid_role_model(self):
        with self.assertRaises(ValueError):
            validated({"planning_model": "unverified-model"})

    def test_token_report_deduplicates_message_ids(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "session.jsonl"
            record = {"message": {"role": "assistant", "id": "m1", "model": "test",
                                   "usage": {"input_tokens": 10, "output_tokens": 5,
                                             "cache_read_input_tokens": 20}}}
            path.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n")
            result = summarize([path])
            self.assertEqual(result["totals"]["calls"], 1)
            self.assertEqual(result["totals"]["cache_read_input_tokens"], 20)

    def test_tool_results_metrics_only_not_content(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "session.jsonl"
            record = {"uuid": "event1", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "tool1", "content": "SECRET_SUPPRESSED"}]}}
            path.write_text(json.dumps(record) + "\n", encoding="utf8")
            data = summarize([path])
            self.assertEqual(data["largest_tool_results"][0]["tool_use_id"], "tool1")
            self.assertEqual(data["largest_tool_results"][0]["bytes"], len("SECRET_SUPPRESSED"))
            self.assertNotIn("SECRET_SUPPRESSED", json.dumps(data))

    def test_haiku_55_price_threshold_is_per_request(self):
        small = estimate_haiku_55_request({"input_tokens": 100000})
        large = estimate_haiku_55_request({"input_tokens": 100001})
        self.assertEqual("up_to_100k", small["pricing_tier"])
        self.assertEqual("over_100k", large["pricing_tier"])
        self.assertEqual(.01, small["minimum_usd"])
        self.assertGreater(large["minimum_usd"], .05)

    def test_haiku_55_cache_ttl_is_reported_as_bounds(self):
        estimate = estimate_haiku_55_request({"cache_creation_input_tokens": 100000})
        self.assertEqual(.0125, estimate["minimum_usd"])
        self.assertEqual(.02, estimate["maximum_usd"])

    def test_usage_streaming_cumulative_max(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "session.jsonl"
            events = [
                {"message":{"id":"m1","role":"assistant","model":"sonnet","usage":{"output_tokens":3}}},
                {"message":{"id":"m1","role":"assistant","model":"sonnet","usage":{"output_tokens":11}}}
            ]
            path.write_text("\n".join(json.dumps(e) for e in events)+"\n", encoding="utf8")
            data = summarize([path])
            self.assertEqual(data["totals"]["output_tokens"],11)
            self.assertEqual(data["totals"]["calls"],1)

if __name__ == "__main__":
    unittest.main()
