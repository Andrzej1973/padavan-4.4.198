#!/usr/bin/env python3
"""Older-created failed run must retain its own artifact without moving latest."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
binary=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='monitor-run-report-') as td:
 root=Path(td);state=root/'state';state.mkdir();fixture=root/'runs.json';log=root/'job.log'
 watermark='2026-11-09T04:12:00Z'
 row=dict(id=42554631707,run_attempt=1,run_number=944,name='Build selected router firmware',
          path='.github/workflows/build-multiple-boards.yml',status='completed',conclusion='failure',
          head_branch='codex/wr1200js-service-webui',head_sha='a'*40,
          created_at='2026-11-09T03:00:00Z',updated_at='2026-11-09T04:20:00Z')
 log.write_text("driver-api-close-entry.inc:6:12: error: 'wr_iot_driver_close_reply' defined but not used [-Werror=unused-function]\n")
 env=dict(os.environ,GITHUB_REPOSITORY='Andrzej1973/padavan-4.4.198',BUILD_MONITOR_FIXTURE_JOB_LOG=str(log))
 def invoke():
  fixture.write_text(json.dumps({'workflow_runs':[row]}))
  return subprocess.run([str(binary),'--fixture:'+str(fixture),'--run-id:'+str(row['id']),
      '--state-dir:'+str(state)],env=env,capture_output=True,text=True,timeout=15,check=True)
 (state/'build-monitor-state.json').write_text(json.dumps({'_last_error_created_at':watermark}))
 (state/'last_build_error.log').write_text('newer sentinel\n')
 result=invoke();assert 'BUILD FAILED:' in result.stdout
 assert (state/'last_build_error.log').read_text()=='newer sentinel\n'
 assert 'unused-function' in (state/'run_build_error.log').read_text()
 assert json.loads((state/'build-monitor-state.json').read_text())['_last_error_created_at']==watermark
 for name in ['last_build_error.log','run_build_error.log']:(state/name).unlink()
 assert 'BUILD FAILED:' not in invoke().stdout
 assert not list(state.glob('*build_error.log'))
 row.update(id=42554631708,conclusion='success')
 assert 'BUILD FAILED:' not in invoke().stdout
 assert not list(state.glob('*build_error.log'))
 row.update(id=42554631709,conclusion='failure')
 assert 'BUILD FAILED:' in invoke().stdout
 assert (state/'run_build_error.log').is_file() and not (state/'last_build_error.log').exists()
print('PASS older explicit run report, latest watermark preservation, cached-state-only job, dedup and success silence')
