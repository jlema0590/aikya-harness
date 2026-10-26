#!/usr/bin/env python3
"""Non-blocking local execution observer; existing permission/document gates stay authoritative."""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[2]
    for runtime in (root/'aikya/scripts/harness',root/'.aikya/runtime'):
        if (runtime/'execution_observer.py').is_file():
            sys.path.insert(0,str(runtime))
            try:
                from execution_observer import main as observe
                return observe(['hook','--root',str(root)])
            except (ValueError,OSError,ImportError):break
    print('NOTICE: Aikya execution visibility unavailable; existing gates remain active.',file=sys.stderr)
    return 0
if __name__=='__main__':raise SystemExit(main())
