#!/usr/bin/env python3
"""Check pinned FT ownership argument threading; execute AUTH callback fixture."""
import argparse
import re
import runpy
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
native = (a.source/'common/ft.c').read_text()
header = (a.source/'include/ft.h').read_text()
schema = runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({}, a.source, here)
enqueue = runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))
_, proto = enqueue['compose'](schema['common/mlme.c'])
_, pending_proto = runpy.run_path(str(here/'ft-pending-enqueue-composition.py'))['compose'](schema['common/mlme.c'])
bounded = runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose'](native)
prepared = enqueue['bind_ft'](bounded, proto, pending_proto)
module = runpy.run_path(str(here/'ft-auth-request-context-composition.py'))
composed, composed_header = module['compose_ft'](prepared, header)


def signatures(text, name):
    return [re.sub(r'\s+', '', value) for value in re.findall(
        r'(?:USHORT|UINT16)\s+'+name+r'\([^)]*\)', text)]


assert signatures(composed, 'FT_AuthReqHandler') == signatures(composed_header, 'FT_AuthReqHandler')
validation = signatures(composed, 'FT_AuthReqRsnValidation')
assert len(validation) == 2 and validation[0] == validation[1]
assert composed.count('pFtInfoBuf,wr_ft_request_context);') == 1
assert composed.count('pFtInfoBuf, &wr_ft_request)') == 1
for name in ('USHORT FT_AuthReqHandler(', 'UINT16\tFT_AuthReqRsnValidation('):
    start = composed.rindex(name)
    body = composed[start:composed.index('\n}', start)+2]
    assert body.index('wr_ft_auth_request_current_locked(') < body.index('pEntry->')
    assert body.index('NdisAcquireSpinLock(') < body.index('wr_ft_auth_request_current_locked(')
    assert body.count('NdisReleaseSpinLock(') == 2
for invalid in (native, composed):
    try:
        module['compose_ft'](invalid, header)
    except ValueError:
        pass
    else:
        raise AssertionError('missing predecessor or duplicate accepted')
drift = prepared.replace('pFtInfoBuf);', 'pFtInfoBuf /* drift */);', 1)
try:
    module['compose_ft'](drift, header)
except ValueError:
    pass
else:
    raise AssertionError('validation call drift accepted')
subprocess.run([sys.executable, str(here/'check-ft-auth-callback.py'), str(a.source),
                '--request-context'], check=True)
print('PASS | FT AUTH invocation context | both caller scopes threaded to native handler and RSN validation; matching declarations; drift and duplicate refusal')
print('PASS | FT AUTH context admission | exact existing/first-peer lease; missing, dual, foreign entry, stale generation and foreign adapter refused; ASan/UBSan callback fixture')
