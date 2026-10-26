"""Conservative migration of known generator/engine assets for explicit SDD opt-in."""
from aikya.resource_paths import source_path
from pathlib import Path
import hashlib
import shutil

SOURCES = {
    "aikya/scripts/harness/sdd_localization.py": "sdd_localization.py",
    "aikya/scripts/harness/scaffold.py": "template/scripts/harness/scaffold.py",
    "aikya/scripts/harness/infrastructure.py": "template/scripts/harness/infrastructure.py",
    "aikya/scripts/harness/sdd_engine.py": "sdd_engine.py",
    "aikya/scripts/harness/sdd_templates.py": "sdd_templates.py"
}
TRUSTED = {
    "aikya/scripts/harness/sdd_localization.py": [
        "0e6024f874e0b070f67707f99f3cc299c44c40ba25a534316d9abc68661e0f15",
        "63d438a66f7eb484bb1982d25d145d793c9063c63e3f70d980412c65f7242392"
    ],
    "aikya/scripts/harness/scaffold.py": [
        "47181c3ad2cb22dbec5567953ae51378e115fcba21c9b590405491ffb990f752",
        "84cb93e758d45f5a1d14fdc0d7fe9ee484366f6e01a241906188f5ccb86413fc",
        "d21ac5a9cf21249e6642bebf56ca2e185f906c84421fe7a226c6533b603fee6f"
    ],
    "aikya/scripts/harness/infrastructure.py": [
        "c26d50ec3369dec6a8589c518c44eae5c246a586b0147d4d12a501d9c2623007",
        "e3f186f10b57c75a5bb8f5a2651376a28775d6a36d53afb9d3055904ea82b2c3",
        "d992701fb2d3cdeaae14aba323dbc8c005f9db384eaf3ac360bf6e9d9ea32d72",
        "f13a5c99a10c1ed48819c9ad22e427828ae0137368f2a65e94fa0d11f2e750a9",
        "17c7b9b8ccbcffb95c67b9ccd88b962108aae9d7e602f6558378bf68b6cdc17d"
    ],
    "aikya/scripts/harness/sdd_engine.py": [
        "c7debd1a2a88336066162b609be19aa778284562f42dedfe51d28bef6f362a8c",
        "8aa568768be4d7acafd63ac3639ebbf8e1f1dcb3c310ece838ae70a3c2216da1",
        "9b883b207148d7e58851062a736f8b8d5ae6f3c492d734dc983bbe0372f97662",
        "811bda89adea8fdbec16cf2ba37241d716953b63a5fc71ec46be5d82cf671863"
    ],
    "aikya/scripts/harness/sdd_templates.py": [
        "8df0334f5aa510965591daa3062b4fa1dc72f3db41fe73e127b50ef6b2f716ad",
        "ade74831ab03432cff6ea1fa815a2d9ac2675fb2bb62f8a4fdf6ac4f4a7f2a06",
        "cfe7302d8b45e9177d2a745b71de486d9ecc40051e378d99eb1a222ad841df2e"
    ]
}


def prepare(root: Path, source: Path) -> list[dict]:
    """Plan exact upgrades, rejecting custom or symlinked code before writes."""
    from aikya.workflows.sdd.engine import rel_file
    from aikya.installation.signatures import predecessor_hashes
    result = []
    for relative, origin in SOURCES.items():
        target = rel_file(root, relative)
        from aikya.installation.assets import resolve_runtime_asset
        current_source = resolve_runtime_asset(source,origin)
        if current_source.source is not None and not current_source.source.is_file(): raise ValueError('Incomplete SDD distribution: ' + origin)
        action = 'CREATE_MANAGED'
        if target.exists():
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if target.read_bytes() == current_source.read_bytes(): action = 'KEEP_EXISTING'
            elif digest in set(TRUSTED[relative]) | predecessor_hashes(source,origin): action = 'UPDATE_KNOWN_SDD_ASSET_WITH_BACKUP'
            else: raise ValueError('Customized generator/engine requires SDD review: ' + relative)
        backup = '.harness/backup-v611/' + relative
        rel_file(root, backup)
        result.append({'path':relative, 'source':current_source, 'action':action, 'backup':backup})
    return result


def apply(root: Path, operations: list[dict], actions: list[str]) -> None:
    for operation in operations:
        if operation['action'] != 'UPDATE_KNOWN_SDD_ASSET_WITH_BACKUP': continue
        target = root/operation['path']; backup = root/operation['backup']
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists(): shutil.copy2(target, backup)
        target.write_bytes(operation['source'].read_bytes())
        actions.append('UPDATED known SDD asset with backup: ' + operation['path'])
