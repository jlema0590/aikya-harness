#!/usr/bin/env python3
"""CI entry point for the static instruction-size proxy."""
import runpy
import sys
sys.dont_write_bytecode = True
if __name__ == '__main__':
    runpy.run_module('aikya.quality.context_budget', run_name='__main__')
