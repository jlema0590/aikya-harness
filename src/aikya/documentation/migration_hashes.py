"""Verified predecessor hashes for conservative upgrades; data is packaged JSON."""
import hashlib
import json
from aikya.resource_paths import source_path,source_root

_path=source_path(source_root(),'migrations/documentation-hashes.json')
_raw=_path.read_bytes()
if hashlib.sha256(_raw).hexdigest()!='5ab1fb4337886a27a034fab8aa53f1a8a782045367c178d99184c519742595f7':
    raise ValueError('Migration hash resource integrity failure')
ASSETS=json.loads(_raw)
