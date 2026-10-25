"""Offline SDK boundary for real default-worker startup, never a provider call."""
from types import SimpleNamespace
import uuid


class ClaudeAgentOptions(SimpleNamespace):
    pass


class HookMatcher(SimpleNamespace):
    pass


class PermissionResultDeny(SimpleNamespace):
    pass


class AssistantMessage(SimpleNamespace):
    pass


class ResultMessage(SimpleNamespace):
    pass


async def query(*, prompt, options):
    # The production worker still builds its real permission/options/schema and
    # serializes these messages. Only the external SDK/provider boundary is fake.
    assert options.permission_mode == 'default'
    assert options.tools == ['Read']
    assert options.mcp_servers == {} and options.skills == []
    assert options.max_turns == 2 and options.max_budget_usd == 0.01
    output = {'candidates': []} if 'candidates' in options.output_format['schema']['properties'] else {'status': 'done', 'approved': True}
    yield AssistantMessage(model='offline-startup-fixture')
    yield ResultMessage(uuid=uuid.uuid4().hex, session_id=uuid.uuid4().hex,
                        is_error=False, subtype='success', terminal_reason='completed',
                        stop_reason=None, structured_output=output, total_cost_usd=0.001,
                        model_usage=None)
