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
    def row(id,attempt=1,conclusion='failure',name='Build selected router firmware',branch='codex/wr1200js-service-webui'):
        return dict(id=id,run_attempt=attempt,run_number=id,name=name,path='.github/workflows/other.yml' if name=='unrelated' else '.github/workflows/build-multiple-boards.yml',status='completed',conclusion=conclusion,head_branch=branch,head_sha='a'*40,created_at=f'2026-10-18T00:00:{id%60:02d}Z',updated_at='2026-10-18T00:01:00Z')
    run([row(2,conclusion='success'),row(1,name='unrelated')]);assert not (state/'last_build_error.log').exists()
    status=json.loads((state/'build-monitor-status.json').read_text())
    assert status['state']=='ok' and status['runs_examined']==2 and status['pid']>0
    # Real run42482744141 had no jobs: reusable actions:read exceeded caller.
    startup_state=root/'workflow-startup'
    startup=row(698,conclusion='startup_failure')
    startup_report=run([startup],target_state=startup_state).stdout
    assert 'BUILD FAILED:' in startup_report and 'Workflow startup/validation failure' in startup_report
    assert 'reusable workflow permissions' in startup_report
    assert 'BUILD FAILED:' not in run([startup],target_state=startup_state).stdout
    startup.update(id=699,conclusion='success')
    assert 'BUILD FAILED:' not in run([startup],target_state=startup_state).stdout
    source_run=row(700);source_run.update(name='Build owned MIPS toolchain',path='.github/workflows/build-owned-toolchain.yml')
    source_state=root/'source-toolchain'
    assert 'BUILD FAILED:' in run([source_run],target_state=source_state).stdout
    assert 'BUILD FAILED:' not in run([source_run],target_state=source_state).stdout
    source_run.update(id=701,conclusion='success')
    assert 'BUILD FAILED:' not in run([source_run],target_state=source_state).stdout
    both=[row(600,branch='main'),row(601),row(602,conclusion='success',branch='main'),row(603,conclusion='success')]
    branch_state=root/'both-branches'
    branch_report=run(both,target_state=branch_state).stdout
    assert branch_report.count('BUILD FAILED:')==2
    assert 'Branch: main\n' in branch_report and 'Branch: codex/wr1200js-service-webui\n' in branch_report
    assert '#602 attempt' not in branch_report and '#603 attempt' not in branch_report
    assert 'BUILD FAILED:' not in run(both,target_state=branch_state).stdout
    r=run([row(432),row(431)]);assert 'BUILD FAILED' in r.stdout
    report=(state/'last_build_error.log').read_text();assert '#432 attempt 1' in report and 'Untrusted diagnostic data' in report
    anchor_log=root/'anchor-change.log'
    anchor_log.write_text('Ralink radio-mode anchor changed\n##[error]Process completed with exit code 1.\n')
    fixture.write_text(json.dumps({'workflow_runs':[row(435)]}),encoding='utf-8')
    anchor_env=dict(os.environ,BUILD_MONITOR_FIXTURE_JOB_LOG=str(anchor_log))
    anchor_result=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'anchor-state')],capture_output=True,text=True,env=anchor_env,check=True)
    assert 'Ralink radio-mode anchor changed' in anchor_result.stdout
    # Real standard42463953909: source download 504 and make error were omitted.
    download_log=root/'libyaml-504.log'
    download_log.write_text("HTTP request sent, awaiting response... 504 Gateway Time-out\nmake[4]: *** [Makefile:10: download_test] Error 4\nmake[3]: *** [Makefile:255: libyaml_only] Error 2\n##[error]Process completed with exit code 2.\n")
    fixture.write_text(json.dumps({'workflow_runs':[row(436)]}),encoding='utf-8')
    download_env=dict(os.environ,BUILD_MONITOR_FIXTURE_JOB_LOG=str(download_log))
    download=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'download-state')],capture_output=True,text=True,env=download_env,check=True)
    assert '504 Gateway Time-out' in download.stdout
    assert 'download_test] Error 4' in download.stdout and 'libyaml_only] Error 2' in download.stdout
    # Preservation42483525613: keep the causal API denial, not only exit 1.
    denied_log=root/'release-403.log'
    denied_log.write_text('HTTP 403: Resource not accessible by integration (https://api.github.com/repos/Andrzej1973/padavan-4.4.198/releases)\n##[error]Process completed with exit code 1.\n')
    fixture.write_text(json.dumps({'workflow_runs':[row(438)]}),encoding='utf-8')
    denied_env=dict(os.environ,BUILD_MONITOR_FIXTURE_JOB_LOG=str(denied_log))
    denied=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'release-denied')],capture_output=True,text=True,env=denied_env,check=True)
    assert 'HTTP 403: Resource not accessible by integration' in denied.stdout
    late_log=root/'late-error.log'
    late_log.write_text('Hunk FAILED at 753.\n'+('routine output\n'*25000)+'ap_cfg.c:15059: error: void value not ignored\n',encoding='utf-8')
    fixture.write_text(json.dumps({'workflow_runs':[row(434)]}),encoding='utf-8')
    late_env=dict(os.environ,BUILD_MONITOR_FIXTURE_JOB_LOG=str(late_log))
    late=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'late-state')],capture_output=True,text=True,timeout=15,env=late_env)
    assert late.returncode==0 and 'void value not ignored' in late.stdout,(late.returncode,late.stdout,late.stderr)
    # A long job may contain old, nonfatal patch failures before the actual
    # failed step. Its final error must remain visible in the bounded suffix.
    # Optional 41760866396: early nonfatal noise obscured a later fixture
    # compiler failure in the deployed default-branch prefix-only monitor.
    late_log.write_text('Hunk FAILED at 753.\n'+('routine output\n'*1300000)+
        "check.c:25:110: error: too few arguments to function 'wr_iot_mcu_message_drop'\n"+
        "apcli_sync.c:1368:4: error: 'bHasWscIe' undeclared (first use in this function)\n"+
        "common/wsc.c:3658:5: error: this 'if' clause does not guard... [-Werror=misleading-indentation]\n"+
        "mcu/andes_mt.c:2308:2: error: ISO C90 forbids mixed declarations and code [-Werror=declaration-after-statement]\n"+
        '##[error]Process completed with exit code 1.\n',encoding='utf-8')
    fixture.write_text(json.dumps({'workflow_runs':[row(435)]}),encoding='utf-8')
    long_job=subprocess.run([str(binary),'--fixture:'+str(fixture),'--state-dir:'+str(root/'long-state')],capture_output=True,text=True,timeout=30,env=late_env)
    assert long_job.returncode==0 and 'Process completed with exit code 1' in long_job.stdout,(long_job.returncode,long_job.stdout[-1000:],long_job.stderr)
    assert 'Hunk FAILED at 753' not in long_job.stdout
    assert "too few arguments to function 'wr_iot_mcu_message_drop'" in long_job.stdout
    assert "'bHasWscIe' undeclared" in long_job.stdout
    assert '[-Werror=misleading-indentation]' in long_job.stdout
    # Optional757 /42038010637: deployed prefix-only report missed this cause.
    assert 'mcu/andes_mt.c:2308:2: error: ISO C90' in long_job.stdout
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
