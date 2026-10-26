#!/usr/bin/env python3
"""Offline executable regression checks: no GitHub writes or notifications."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from contextlib import nullcontext

binary=Path(sys.argv[1]).resolve()
with (nullcontext(sys.argv[2]) if len(sys.argv)>2 else tempfile.TemporaryDirectory(prefix='nim-monitor-')) as temporary:
    root=Path(temporary);fixture=root/'runs.json';state=root/'state'
    def run(runs,expected=0,target_state=None):
        fixture.write_text(json.dumps({'workflow_runs':runs}),encoding='utf-8')
        r=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(target_state or state)],capture_output=True,text=True,timeout=15)
        assert r.returncode==expected,(r.returncode,r.stdout,r.stderr)
        return r
    def row(id,attempt=1,conclusion='failure',name='Build selected router firmware'):
        return dict(id=id,run_attempt=attempt,run_number=id,name=name,path='.github/workflows/other.yml' if name=='unrelated' else '.github/workflows/build-multiple-boards.yml',status='completed',conclusion=conclusion,head_sha='a'*40,created_at=f'2026-10-18T00:00:{id%60:02d}Z',updated_at='2026-10-18T00:01:00Z')
    run([row(2,conclusion='success'),row(1,name='unrelated')]);assert not (state/'last_build_error.log').exists()
    status=json.loads((state/'build-monitor-status.json').read_text())
    assert status['state']=='ok' and status['runs_examined']==2 and status['pid']>0
    r=run([row(432),row(431)]);assert 'BUILD FAILED' in r.stdout
    report=(state/'last_build_error.log').read_text();assert '#432 attempt 1' in report and 'Untrusted diagnostic data' in report
    late_log=root/'late-error.log'
    late_log.write_text('Hunk FAILED at 753.\n'+('routine output\n'*25000)+'ap_cfg.c:15059: error: void value not ignored\n',encoding='utf-8')
    fixture.write_text(json.dumps({'workflow_runs':[row(434)]}),encoding='utf-8')
    late_env=dict(os.environ,BUILD_MONITOR_FIXTURE_JOB_LOG=str(late_log))
    late=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'late-state')],capture_output=True,text=True,timeout=15,env=late_env)
    assert late.returncode==0 and 'void value not ignored' in late.stdout,(late.returncode,late.stdout,late.stderr)
    # A long job may contain old, nonfatal patch failures before the actual
    # failed step. Its final error must remain visible in the bounded suffix.
    late_log.write_text('Hunk FAILED at 753.\n'+('routine output\n'*1300000)+'##[error]Process completed with exit code 1.\n',encoding='utf-8')
    fixture.write_text(json.dumps({'workflow_runs':[row(435)]}),encoding='utf-8')
    long_job=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'long-state')],capture_output=True,text=True,timeout=30,env=late_env)
    assert long_job.returncode==0 and 'Process completed with exit code 1' in long_job.stdout,(long_job.returncode,long_job.stdout[-1000:],long_job.stderr)
    assert 'Hunk FAILED at 753' not in long_job.stdout
    previous=(state/'last_build_error.log').read_bytes()
    assert 'BUILD FAILED' not in run([row(432),row(431)]).stdout
    assert (state/'last_build_error.log').read_bytes()==previous
    run([row(432,2)]);assert 'attempt 2' in (state/'last_build_error.log').read_text()
    older=row(501);older['created_at']='2026-10-18T00:00:01Z';older['updated_at']='2026-10-18T00:10:00Z'
    newer=row(502);newer['created_at']='2026-10-18T00:00:02Z';newer['updated_at']='2026-10-18T00:03:00Z'
    order_state=root/'out-of-order-state'
    run([newer,older],target_state=order_state)
    assert '#502 attempt 1' in (order_state/'last_build_error.log').read_text(), 'older slow run overwrote newer failure'
    order_data=json.loads((order_state/'build-monitor-state.json').read_text())
    assert order_data['_last_error_created_at']=='2026-10-18T00:00:02Z'
    assert not (state/'build-monitor.lock').exists()
    fixture.write_text('{broken json')
    failed=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(state)],capture_output=True,text=True,timeout=15)
    assert failed.returncode==1 and not (state/'build-monitor.lock').exists()
    assert 'attempt 2' in (state/'last_build_error.log').read_text()
    (state/'build-monitor.lock').mkdir();run([row(433)],1)
    assert 'attempt 2' in (state/'last_build_error.log').read_text()
print('PASS monitor executable: workflow filtering, latest failure, retry attempts, deduplication, lock refusal and report retention; offline fixtures only')
