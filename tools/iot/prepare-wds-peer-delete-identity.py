#!/usr/bin/env python3
"""Reject WDS deletion address mismatch before vendor side effects."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
pins={
 'include/wr-iot-wds-peer-delete-gate.inc':'4bb3759098b87bc19060311754d58fb1b1c0326e3fd9524a48e82e1e901038b5',
 'mgmt/mgmt_entrytb.c':'484a3f573d37da90445373e7fddd9ac0cd8c5d32a39012dded66e08bd140a504',
}
for name,digest in pins.items():
    actual=hashlib.sha256((src/name).read_bytes()).hexdigest()
    allowed={digest}
    if name=='include/wr-iot-wds-peer-delete-gate.inc':
        # The full chain now installs the reviewed identity gate at its first
        # insertion. Also accept that exact version; do not relax source pins.
        allowed.add('87373ae3622c348ea2605c6d005f3b810489db7b847a0d70c4b6b8e9c1efe8d0')
        allowed.add('37adf1e8fb2f0f097d84c832b7888b904d9ecdb9a55f866b05f8d68dce7a42a3')
    if actual not in allowed:
        p.error('unreviewed deletion input: '+name)
    pins[name]=actual
receipt=json.loads(src.with_name(src.name+'-retirement-close.json').read_text())
for name,digest in receipt['output_sha256'].items():
    if hashlib.sha256((src/'include'/name).read_bytes()).hexdigest()!=digest:
        p.error('close-gate predecessor mismatch: '+name)
helper=Path(__file__).with_name('wds-peer-delete-gate.inc')
shutil.copytree(src,out)
shutil.copyfile(helper,out/'include/wr-iot-wds-peer-delete-gate.inc')
out.with_name(out.name+'-delete-identity.json').write_text(json.dumps({
 'input_sha256':pins,
 'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
 'scope':'WDS-only early address refusal; age-out reservation/terminal-state validation still open',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged WDS deletion identity gate before timer/vendor mutation')
