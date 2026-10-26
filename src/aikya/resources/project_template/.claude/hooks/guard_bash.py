#!/usr/bin/env python3
"""Defensa parcial frente a comandos de Bash manifiestamente peligrosos.

La política de permisos y los controles humanos siguen siendo necesarios.
"""
import json
import re
import sys

BLOCK = (
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard requiere una revisión humana"),
    (r"\bgit\s+push\b[^\n;|]*\s(?:--force(?:-with-lease)?|-f)(?:\s|$)", "force push bloqueado"),
    (r"\bterraform\s+destroy\b", "terraform destroy bloqueado"),
    (r"\bkubectl\s+delete\b", "kubectl delete bloqueado"),
    (r"\brm\s+-[^\s]*r[^\s]*f[^\s]*\s+(?:/|~|\$HOME)(?:\s|/|$)", "borrado recursivo masivo bloqueado"),
    (r"\bcurl\b[^\n|]*\|\s*(?:sudo\s+)?(?:bash|sh)\b", "ejecución remota por pipe bloqueada"),
)

def decide(command: str):
    for pattern, reason in BLOCK:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return reason
    return None

def main():
    try:
        event = json.load(sys.stdin)
        command = str(event.get('tool_input', {}).get('command', ''))
    except (ValueError, TypeError, AttributeError):
        # Denegar cuando no puede evaluarse la entrada.
        command = ''
        reason = 'Hook de seguridad: entrada JSON inválida'
    else:
        reason = decide(command)
    if reason:
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName':'PreToolUse',
            'permissionDecision':'deny',
            'permissionDecisionReason':reason
        }}))
    return 0

if __name__ == '__main__':
    sys.exit(main())
