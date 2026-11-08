#!/usr/bin/env python3
"""Regression for full bundle closure and target-probe duplicate include guard."""
from pathlib import Path
import runpy,tempfile,shutil
here=Path(__file__).resolve().parent
resolve=runpy.run_path(str(here/'close-bundle-assets.py'))['dependencies']
closure=resolve(here)
assert 'driver-api-close-completion.h' in closure
assert 'driver-api-close-synchronous-put.h' in closure
with tempfile.TemporaryDirectory(prefix='wr-bundle-assets-') as d:
 root=Path(d)
 for name in closure:shutil.copyfile(here/name,root/name)
 assert resolve(root)==closure
 (root/'driver-api-close-completion.h').unlink()
 try:resolve(root)
 except ValueError as exc:assert 'driver-api-close-completion.h' in str(exc)
 else:raise AssertionError('Missing transitive completion header accepted')
probe=runpy.run_path(str(here/'check-close-bindings-target-tu.py'))['probe_source'](Path('/driver'),here)
assert probe.index('/driver/os/linux/rt_main_dev.c')<probe.index('#ifndef WR_IOT_DRIVER_CLOSE_BUNDLE_H')
assert probe.count('#ifndef WR_IOT_DRIVER_CLOSE_BUNDLE_H')==1
print('PASS full CLOSE bundle closure, missing transitive header refusal, probe duplicate guard; no target build claim')

integrate=runpy.run_path(str(here/'close-bundle-assets.py'))['integrate']
with tempfile.TemporaryDirectory(prefix='wr-bundle-integrate-') as d:
 source=Path(d)/'source';(source/'include').mkdir(parents=True)
 (source/'include/radio-transition.h').write_text('prior generated transition\n')
 edits={'os/linux/rt_main_dev.c':'before\n#include "driver-api-closed-entry.inc"\nafter\n',
        'include/radio-transition-api.h':'extended successor transition\n'}
 before=dict(edits)
 result=integrate(edits,source,here,'os/linux/rt_main_dev.c')
 assert edits==before
 assert 'include/driver-api-close-completion.h' in result
 assert result['include/radio-transition-api.h']==edits['include/radio-transition-api.h']
 assert 'include/radio-transition.h' not in result
 assert (source/'include/radio-transition.h').read_text()=='prior generated transition\n'
 entry=result['os/linux/rt_main_dev.c']
 assert entry.index('#include "driver-api-close-bundle.h"')<entry.index('#include "driver-api-closed-entry.inc"')
 assert 'case 10' not in entry and 'case 13' not in entry
 try:integrate(result,source,here,'os/linux/rt_main_dev.c')
 except ValueError:pass
 else:raise AssertionError('Duplicate ordinary TU integration accepted')
 broken=dict(edits);broken['os/linux/rt_main_dev.c']='missing anchor'
 try:integrate(broken,source,here,'os/linux/rt_main_dev.c')
 except ValueError:pass
 else:raise AssertionError('Missing include anchor accepted')
 assert edits==before
print('PASS actual integration function: missing transitive copied, generated shared headers preserved, immutable input, duplicate/missing anchors refuse; no dispatch')
