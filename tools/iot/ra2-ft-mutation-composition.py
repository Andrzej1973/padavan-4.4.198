"""Prepare full FT action mutation wrapper; deliberately not producer-installed.

Receiver-only classification is insufficient for native cross-BSS lookups.
This prepares the balanced outer seam, not a complete safe FT implementation.
"""
import runpy
from pathlib import Path

def compose(source):
    module=runpy.run_path(str(Path(__file__).with_name('ra2-mutation-wrappers.py')))
    # compose's globals own SITES; isolate this invocation from the production
    # auth/association site list and preserve its exact wrapper generator.
    module['compose'].__globals__['SITES']={'common/ft.c':[('FT_FtAction',False,False)]}
    return module['compose']('common/ft.c',source)
