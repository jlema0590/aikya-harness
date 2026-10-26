"""One application-level owner for launchers shared across registration scopes."""
import json
import os
from pathlib import Path
import shutil
from . import state


def publish(root, candidate):
    marker = state.safe(root / 'launchers.json')
    previous = json.loads(marker.read_text(encoding='utf8')) if marker.exists() else {}
    destination_root = root / 'bin'
    for name in ('aikya', 'aikya-setup', 'aikya-manage'):
        filename = name + ('.exe' if os.name == 'nt' else '')
        destination = state.safe(destination_root / filename)
        current = state.snapshot([destination]).get(str(destination))
        if current is not None and current != previous.get(str(destination)):
            raise ValueError('Customized application launcher requires review: ' + str(destination))
        origin = candidate / ('Scripts' if os.name == 'nt' else 'bin') / filename
        destination_root.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(origin, destination)
        except PermissionError:
            if os.name != 'nt' or filename != 'aikya-manage.exe' or current is None:
                raise
            print('Management launcher is in use; its compatible previous environment is retained.')
    state.write_json(marker, state.snapshot([destination_root]))


def remove(root):
    marker = state.safe(root / 'launchers.json')
    owned = json.loads(marker.read_text(encoding='utf8')) if marker.exists() else {}
    for name in owned:
        if Path(name).parent != root / 'bin':
            raise ValueError('Unsafe launcher ownership record')
    preserved = state.restore({}, owned)
    if not preserved:
        marker.unlink(missing_ok=True)
    return preserved
