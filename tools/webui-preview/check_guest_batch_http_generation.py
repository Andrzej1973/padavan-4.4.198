#!/usr/bin/env python3
"""Fresh pinned-source composition check of the complete candidate HTTP chain."""
import hashlib
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-guest-batch-http-source-') as scratch:
    root=Path(scratch)
    with tarfile.open(sys.argv[1]) as archive:
        for name in ('httpd/web_ex.c','httpd/httpd.c','httpd/cgi.c','httpd/variables.c','shared/defaults.c'):
            target=root/'trunk/user'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile('trunk/user/'+name).read())
    tools=(here.parent/'prepare-shared-wifi.py',here/'prepare-password-candidate.py',
           here/'prepare-guest-candidate.py',here/'prepare-guest-transport.py',
           here/'prepare-modern-body.py',here/'prepare-guest-json.py',here/'prepare-guest-batch-http.py')
    for tool in tools:
        subprocess.run(['python3',str(tool),str(root)],check=True)
    web=root/'trunk/user/httpd/web_ex.c'
    source=web.read_text()
    assert source.count((here/'guest-batch-http.c.inc').read_text())==1
    marker='static void do_wr_modern_guest_apply('
    start=source.index(marker);end=source.index('\n}',start)+2
    handler=source[start:end]
    assert handler.count('wr_nvram_submit_batch(')==1
    assert 'update_variables_ex(' not in handler and 'nvram_set(' not in handler
    assert handler.index('wr_nvram_submit_batch(')<handler.index('stored=nvram_safe_get(')<handler.index('asus_nvram_commit(')<handler.index('ej_notify_services(')
    for name in ('guest-batch.h','nvram-batch-client.h','nvram-batch-wire.h'):
        assert (root/'trunk/user/httpd/wr-shared-wifi'/name).read_bytes()==(here/name).read_bytes()
    fields=re.findall(r'"([a-z0-9_]+)"',(here/'guest-adapter.h').read_text().split('wr_modern_guest_fields[]={',1)[1].split('};',1)[0])
    variables=(root/'trunk/user/httpd/variables.c').read_text()
    rows=re.findall(r'\{"((?:rt|wl)_guest_[^"]+)",\s*"",\s*NULL,\s*([^}]+)\}',variables)
    assert len(rows)==28 and len(fields)==14
    assert dict(rows)=={band+'_guest_'+field:'EVM_RESTART_WIFI'+number for band,number in [('rt','2'),('wl','5')] for field in fields}
    before=web.read_bytes()
    repeated=subprocess.run(['python3',str(tools[-1]),str(root)],capture_output=True)
    assert repeated.returncode and web.read_bytes()==before
    print('PASS fresh pinned HTTP chain, actual28 Guest variable/event rows, one batch/no legacy fallback, readback before commit/notify, repeated preparation rejected; C host bodies tested separately')
    print('Candidate web_ex SHA256',hashlib.sha256(before).hexdigest())
    print('Owned scratch bytes removed',sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
assert not root.exists()
