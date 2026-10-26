"""Compatibility and safety regressions for Haiku 5.5 hybrid routing."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aikya.routing.policy import (DEFAULT, HAIKU_45, HAIKU_55, validated,
                          resolved_agent_model, auxiliary_ready)
from aikya.routing.models import parse_cli_version, capability_status
from aikya.routing.router import route, semantic_advice
from aikya.catalogs import engineering as engineering_catalog

def enabled_policy(**overrides):
    return {**DEFAULT, "auxiliary_enabled": True, "user_approved": True,
            "model_access_confirmed": True, **overrides}

class LegacyCompatibilityTests(unittest.TestCase):
    def test_591_no_policy_keeps_routine_inherit(self):
        policy = validated(None)
        self.assertEqual(resolved_agent_model("planner", policy), "opus")
        self.assertEqual(resolved_agent_model("java-developer", policy), "inherit")
        self.assertFalse(auxiliary_ready(policy))

    def test_existing_v1_haiku_45_never_silently_upgrades(self):
        policy = validated({"schema_version": 1, "auxiliary_model": HAIKU_45,
                            "auxiliary_enabled": True, "user_approved": True})
        self.assertEqual(policy["schema_version"], 1)
        self.assertEqual(resolved_agent_model("log-summarizer", policy), HAIKU_45)
        self.assertEqual(resolved_agent_model("aikya-auxiliary-analyzer", policy), "inherit")

    def test_legacy_v1_explicit_haiku_alias_keeps_behavior(self):
        policy = validated({"schema_version": 1, "auxiliary_model": "haiku",
                            "auxiliary_enabled": True, "user_approved": True})
        self.assertEqual(resolved_agent_model("log-summarizer", policy), "haiku")

    def test_existing_v1_no_auxiliary_opt_in(self):
        p = validated({"schema_version": 1, "auxiliary_enabled": False})
        self.assertEqual(resolved_agent_model("log-summarizer", p), "inherit")

class NewPolicyTests(unittest.TestCase):
    def test_haiku_55_is_new_disabled_default(self):
        self.assertEqual(DEFAULT["auxiliary_model"], HAIKU_55)
        self.assertFalse(DEFAULT["auxiliary_enabled"])

    def test_consent_is_mandatory(self):
        with self.assertRaises(ValueError):
            validated({"schema_version": 2, "auxiliary_enabled": True})

    def test_provider_alias_is_rejected(self):
        with self.assertRaises(ValueError):
            validated({"schema_version": 2, "auxiliary_model": "haiku"})

    def test_45_in_v2_is_rejected_not_overwritten(self):
        with self.assertRaises(ValueError):
            validated({"schema_version": 2, "auxiliary_model": HAIKU_45})

    def test_readonly_delegation_depth_and_task_permissions(self):
        for values in ({"require_read_only": False},
                       {"max_delegation_depth": 3},
                       {"allowed_tasks": ["terraform-apply"]},
                       {"confidence_threshold": 1.5}):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    validated({**DEFAULT, **values})

    def test_opted_in_agent_models_and_critical_inherit(self):
        p = validated(enabled_policy())
        self.assertTrue(auxiliary_ready(p, "classification"))
        self.assertEqual(resolved_agent_model("aikya-auxiliary-analyzer", p), HAIKU_55)
        self.assertEqual(resolved_agent_model("aikya-docs-assistant", p), HAIKU_55)
        self.assertEqual(resolved_agent_model("security-reviewer", p), "inherit")
        self.assertEqual(resolved_agent_model("terraform-engineer", p), "inherit")

    def test_provider_and_unconfirmed_fallback(self):
        for policy in (enabled_policy(model_provider="bedrock"),
                       enabled_policy(model_access_confirmed=False),
                       enabled_policy(routing_mode="deterministic")):
            self.assertFalse(auxiliary_ready(policy))
            self.assertEqual(resolved_agent_model("log-summarizer", policy), "inherit")

    def test_capability_probe_never_fakes_live_access(self):
        self.assertEqual(parse_cli_version("2.1.293 (Claude Code)"), (2, 1, 293))
        self.assertFalse(capability_status(enabled_policy(), "2.1.292")["ready_for_cli_delegation"])
        status = capability_status(enabled_policy(), "2.1.293")
        self.assertTrue(status["ready_for_cli_delegation"])
        self.assertIn("do not prove", status["note"])

class RouterTests(unittest.TestCase):
    def test_new_java_api_uses_planner_if_multicomponent(self):
        r = route("Crear API Java Spring Boot de pedidos", affected_components=4)
        self.assertEqual(r["category"], "feature")
        self.assertEqual(r["recommended_role"], "planner")
        self.assertEqual(r["recommended_model"], "opus")

    def test_api_feature_with_tests_and_docs_is_still_a_feature(self):
        result = route("Implementa API Java con pruebas y documentación")
        self.assertEqual(result["category"], "feature")
        self.assertEqual(result["specialist"], "java-developer")

    def test_flutter_bug_avoids_opus(self):
        r = route("Corrige botón favoritos Flutter", affected_components=1)
        self.assertEqual(r["recommended_role"], "flutter-developer")
        self.assertEqual(r["recommended_model"], "inherit")

    def test_devops_complex_uses_orchestrator(self):
        r = route("Crear pipeline GitHub Actions Helm Kubernetes",
                  affected_components=4)
        self.assertEqual(r["recommended_role"], "orchestrator")

    def test_azure_terraform_safe_vs_apply(self):
        safe = route("Crear módulos Terraform Azure", affected_components=1)
        self.assertEqual(safe["recommended_role"], "terraform-engineer")
        danger = route("Ejecuta terraform apply en production", affected_components=1)
        self.assertTrue(danger["requires_approval"])
        self.assertTrue(danger["risk_flag"])
        self.assertIsNone(danger["auxiliary_agent"])

    def test_semantic_json_is_untrusted(self):
        self.assertIsNone(semantic_advice(
            {"category":"feature", "confidence":1, "suggested_role":"developer",
             "tools":["Bash"]}, .85))
        self.assertIsNone(semantic_advice(
            {"category":"feature", "confidence":.6, "suggested_role":"developer"}, .85))

    def test_haiku_only_advises_under_approved_policy(self):
        self.assertIsNone(route("Ayúdame a revisar esto")["auxiliary_agent"])
        with patch("aikya.routing.models.inspect_cli", return_value={"version":"2.1.293"}):
            enabled = route("Ayúdame a revisar esto", enabled_policy())
        self.assertEqual(enabled["auxiliary_agent"], "aikya-auxiliary-analyzer")
        self.assertEqual(enabled["auxiliary_task"], "classification")
        self.assertIn("no LLM invoked", enabled["note"])

    def test_ambiguous_low_risk_semantic_advice(self):
        advice = {"category": "testing", "confidence": .94,
                  "suggested_role": "test-engineer", "requires_planning": False}
        with patch("aikya.routing.models.inspect_cli", return_value={"version":"2.1.293"}):
            r = route("Ayúdame con esto", enabled_policy(), semantic=advice)
        self.assertEqual(r["recommended_role"], "test-engineer")
        self.assertTrue(r["semantic_advice_accepted"])

    def test_high_risk_does_not_delegate_to_haiku(self):
        r = route("Configura production secrets", enabled_policy())
        self.assertIsNone(r["auxiliary_agent"])
        self.assertTrue(r["requires_approval"])

class CatalogTests(unittest.TestCase):
    def test_no_haiku_agents_in_legacy_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selected = engineering_catalog.discover(root, {"backend":"java"}, [])
            self.assertNotIn("aikya-auxiliary-analyzer", selected["agents"])
            self.assertNotIn("aikya-docs-assistant", selected["agents"])

    def test_approved_v2_can_select_agents_when_cli_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/".aikya").mkdir()
            (root/".aikya/model-policy.json").write_text(json.dumps(enabled_policy()))
            with patch("aikya.routing.models.inspect_cli",
                       return_value={"version":"2.1.293"}):
                selected = engineering_catalog.discover(root, {"backend":"java"}, [])
            for name in ("aikya-auxiliary-analyzer", "aikya-docs-assistant",
                         "log-summarizer"):
                self.assertIn(name, selected["agents"])

    def test_unavailable_cli_refuses_new_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/".aikya").mkdir()
            (root/".aikya/model-policy.json").write_text(json.dumps(enabled_policy()))
            with patch("aikya.routing.models.inspect_cli",
                       return_value={"version":None}):
                selected = engineering_catalog.discover(root, {"backend":"java"}, [])
            self.assertNotIn("aikya-auxiliary-analyzer", selected["agents"])

if __name__ == "__main__":
    unittest.main()
