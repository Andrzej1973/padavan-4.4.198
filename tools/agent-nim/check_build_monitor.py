#!/usr/bin/env python3
"""Offline executable regression checks: no GitHub writes or notifications."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from contextlib import nullcontext

binary=Path(sys.argv[1]).resolve()
with (nullcontext(sys.argv[2]) if len(sys.argv)>2 else tempfile.TemporaryDirectory(prefix='nim-monitor-')) as temporary:
    root=Path(temporary);fixture=root/'runs.json';state=root/'state'
    def run(runs,expected=0):
        fixture.write_text(json.dumps({'workflow_runs':runs}),encoding='utf-8')
        r=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(state)],capture_output=True,text=True,timeout=15)
        assert r.returncode==expected,(r.returncode,r.stdout,r.stderr)
        return r
    def row(id,attempt=1,conclusion='failure',name='Build selected router firmware'):
        return dict(id=id,run_attempt=attempt,run_number=id,name=name,path='.github/workflows/other.yml' if name=='unrelated' else '.github/workflows/build-multiple-boards.yml',status='completed',conclusion=conclusion,head_sha='a'*40,updated_at='2026-10-18T00:00:00Z')
    run([row(2,conclusion='success'),row(1,name='unrelated')]);assert not (state/'last_build_error.log').exists()
    r=run([row(432),row(431)]);assert 'BUILD FAILED' in r.stdout
    report=(state/'last_build_error.log').read_text();assert '#432 attempt 1' in report and 'Untrusted diagnostic data' in report
    previous=(state/'last_build_error.log').read_bytes()
    assert 'BUILD FAILED' not in run([row(432),row(431)]).stdout
    assert (state/'last_build_error.log').read_bytes()==previous
    run([row(432,2)]);assert 'attempt 2' in (state/'last_build_error.log').read_text()
    assert not (state/'build-monitor.lock').exists()
    fixture.write_text('{broken json')
    failed=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(state)],capture_output=True,text=True,timeout=15)
    assert failed.returncode==1 and not (state/'build-monitor.lock').exists()
    assert 'attempt 2' in (state/'last_build_error.log').read_text()
    (state/'build-monitor.lock').mkdir();run([row(433)],1)
    assert 'attempt 2' in (state/'last_build_error.log').read_text()
print('PASS monitor executable: workflow filtering, latest failure, retry attempts, deduplication, lock refusal and report retention; offline fixtures only')
