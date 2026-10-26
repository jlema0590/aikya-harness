"""Proportional phase recipes for public Aikya commands; never grants permissions."""
from aikya.workflows.methodology import normalize_methodology
PHASES=('explore','plan','implement','validate','security','review')
LABELS={name:name.title() for name in PHASES}
READ_ONLY=frozenset(('aikya-tokens','aikya-skills-status','aikya-skills-plan','aikya-sdd-status','aikya-doctor'))

def recipe(command: str, methodology='odd', *, preview=False, security_required=None, review_required=False):
    from aikya.cli.commands import BOOTSTRAP_COMMANDS
    if not isinstance(command,str):raise ValueError('Invalid command')
    command=command.removeprefix('/')
    if command not in BOOTSTRAP_COMMANDS:raise ValueError('Unknown Aikya command')
    method=normalize_methodology(methodology)
    read_only=preview or command in READ_ONLY or command=='aikya-arc-review'
    required=['explore']
    if command not in READ_ONLY:required.append('plan')
    if not read_only:required.append('implement')
    required.append('validate')
    if security_required is None:security_required=not read_only and command not in ('aikya-docs','aikya-docs-sync')
    if security_required:required.append('security')
    if review_required or command=='aikya-arc-review':required.append('review')
    return {'command':command,'methodology':method,'phases':list(PHASES),'required':required,
            'read_only':read_only,'note':'Applicability is recorded; phases never grant approvals.'}
