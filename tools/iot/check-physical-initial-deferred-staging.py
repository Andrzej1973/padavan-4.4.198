"""Compose existing deferred driver installer with INITIAL_OFF storage staging."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-stop-candidate.py')}
source=(here/'check-physical-stop-candidate.py').read_text()
exec(compile(source[:source.index("with tempfile.TemporaryDirectory(")],'<reviewed fixture setup>','exec'),ns)
files=dict(ns['files'])
files['include/wr-iot-raw-recovery-free-fence.inc']=(here/'raw-recovery-free-fence.inc').read_text()
files['include/driver-api-closed-entry.inc']='#define WR_IOT_RA2_NO_HOST_MODE 1\n'+(here/'driver-api-closed-entry.inc').read_text()
files['include/wr-iot-reset-admission.inc']=(here/'reset-admission.inc').read_text()
files['os/linux/rt_main_dev.c']=(here/'main-close-checked.inc').read_text()
files['include/main-open-recovery-owner.h']=(here/'main-open-recovery-owner.h').read_text()
with tempfile.TemporaryDirectory(prefix='wr-stop-deferred-installer-') as d:
 root=Path(d);src=root/'source';src.mkdir()
 for n,text in files.items():
  f=src/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
 hashes=lambda:{n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in files}
 before=hashes()
 manifest={'production_installed':False,'merged_driver_sha256':before,
 'candidate_driver_sha256':dict(before),'main_physical_close_delegation_layer':{'physical_close_delegated':True},'ra2_no_host_experiment':{}}
 src.with_name(src.name+'.manifest.json').write_text(json.dumps(manifest))
 def run(inp,out,ok):
  r=subprocess.run([sys.executable,'-B',str(here/'prepare-physical-stop-deferred-candidate.py'),str(inp),str(out)],capture_output=True,text=True)
  assert (r.returncode==0)==ok,r.stderr
 missing=dict(manifest);missing.pop('ra2_no_host_experiment')
 src.with_name(src.name+'.manifest.json').write_text(json.dumps(missing))
 run(src,root/'missing-no-host',False);assert not (root/'missing-no-host').exists()
 src.with_name(src.name+'.manifest.json').write_text(json.dumps(manifest))
 out=root/'prepared';run(src,out,True)
 import runpy
 prepare_initial=runpy.run_path(str(here/'prepare-physical-initial-storage.py'))['prepare']
 initial=root/'initial-prepared'
 prepared_hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
 initial_report=prepare_initial(out,initial)
 assert prepared_hashes=={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
 assert initial_report['initial_storage_and_retirement_staged'] and not initial_report['endpoint_installed']
 header=(initial/'include/rtmp.h').read_text()
 assert '#include "physical-initial-types.h"' in header
 assert 'struct wr_iot_physical_initial_record wr_iot_physical_initial;' in header
 assert 'struct wr_iot_physical_initial_terminal wr_iot_physical_initial_terminal;' in header
 for name in initial_report['helpers_sha256']:
  assert hashlib.sha256((initial/'include'/name).read_bytes()).hexdigest()==initial_report['helpers_sha256'][name]
 assert 'wr_iot_physical_initial_terminal_clear(&initial)' in (initial/'include/wr-iot-raw-recovery-free-fence.inc').read_text()
 assert (initial/'os/linux/rt_main_dev.c').read_bytes()==(out/'os/linux/rt_main_dev.c').read_bytes()

 # Compose optional worker integration in a fresh copy; source remains immutable.
 bound=root/'initial-bound'
 bound_report=prepare_initial(out,bound,bind_main=True)
 assert bound_report['main_worker_initial_bound'] and not bound_report['endpoint_installed']
 worker=(bound/'os/linux/rt_main_dev.c').read_text()
 assert '#include "physical-initial-record.h"' in worker
 assert 'physical_armed && initial_origin' in worker
 assert 'physical_armed && !initial_origin' in worker
 assert 'wr_iot_physical_initial_record_running' in worker
 for helper in ('physical-initial-record.h','physical-initial-origin.h','precreated-idle-probe.h','precreated-idle-reference.h'):
  assert (bound/'include'/helper).read_bytes()==(here/helper).read_bytes()
 assert prepared_hashes=={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
 try:prepare_initial(bound,root/'initial-duplicate',bind_main=True)
 except ValueError:pass
 else:raise AssertionError('duplicate initial integration accepted')
 assert not (root/'initial-duplicate').exists()
 endpoint=root/'initial-endpoint'
 endpoint_report=prepare_initial(out,endpoint,bind_main=True,install_endpoint=True)
 assert endpoint_report['endpoint_installed'] and endpoint_report['main_worker_initial_bound']
 dispatch=(endpoint/'include/driver-api-closed-entry.inc').read_text()
 for route in ('physical_initial','physical_stop','physical_rebind'):
  assert dispatch.count('return wr_iot_'+route+'_ioctl(ad,dev,rq);')==1
 assert '#include "physical-initial-handler.inc"' in dispatch
 assert '#include "physical-initial-terminal-replace.inc"' in dispatch
 assert 'physical-initial-terminal-replace.inc' in endpoint_report['helpers_sha256']
 endpoint_manifest=json.loads(endpoint.with_name(endpoint.name+'.manifest.json').read_text())
 assert endpoint_manifest['initial_physical_layer']['request_magic']=='WPIQ'
 assert endpoint_manifest['production_installed'] is False
 assert endpoint_manifest['merged_driver_sha256']=={str(p.relative_to(endpoint)):hashlib.sha256(p.read_bytes()).hexdigest() for p in endpoint.rglob('*') if p.is_file()}
 dispatch_compose=runpy.run_path(str(here/'physical-initial-dispatch.py'))['compose']
 try:dispatch_compose(dispatch)
 except ValueError:pass
 else:raise AssertionError('duplicate endpoint dispatch accepted')
 original_dispatch=(out/'include/driver-api-closed-entry.inc').read_text()
 for guard in ('if(!rtnl_is_locked())return -EBUSY;', 'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;'):
  try:dispatch_compose(original_dispatch.replace(guard,'',1))
  except ValueError:pass
  else:raise AssertionError('missing authorization guard accepted')
 try:prepare_initial(out,root/'endpoint-without-main',install_endpoint=True)
 except ValueError:pass
 else:raise AssertionError('endpoint without worker accepted')
 assert not (root/'endpoint-without-main').exists()
 assert prepared_hashes=={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
 assert hashes()==before
 raw=(out/'include/wr-iot-raw-recovery-free-fence.inc').read_text()
 assert 'wr_iot_physical_lifetime.active' in raw
 assert 'wr_iot_physical_stop_terminal_clear(&terminal)' in raw
 assert raw.index('RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);')<raw.index('wr_iot_physical_stop_terminal_clear(&terminal)')

 assert 'struct wr_iot_physical_rebind_probe wr_iot_physical_rebind_probe;' in (out/'include/rtmp.h').read_text()
 assert (out/'common/rtmp_init.c').read_text().count('NdisZeroMemory(&pAd->wr_iot_physical_rebind_probe,')==1
 assert (out/'include/physical-rebind-probe-types.h').is_file()
 assert (out/'include/physical-rebind-probe.h').is_file()
 binding=(out/'include/physical-rebind-binding.inc').read_text()
 assert binding.count('task_pid(current)')==3
 assert binding.index('RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);')<binding.index('observed=wr_iot_mt7603_closed_config_observed(ad,dev);')
 assert '#include "physical-rebind-binding.inc"' in (out/'include/driver-api-closed-entry.inc').read_text()

 for name in ('include/wr-iot-mbss-recovery-work.inc','include/wr-iot-mbss-recovery-join.inc'):
  assert 'ad->wr_iot_physical_rebind_probe.active' in (out/name).read_text()
 assert 'ad->wr_iot_physical_rebind_probe.active' in raw
 assert 'struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;' in (out/'include/rtmp.h').read_text()
 assert (out/'common/rtmp_init.c').read_text().count('NdisZeroMemory(&pAd->wr_iot_physical_terminal,')==1

 for field in ('wr_iot_physical_pins','wr_iot_physical_pending_pins'):
  assert ('struct wr_iot_physical_stop_pins '+field+';') in (out/'include/rtmp.h').read_text()
  assert (out/'common/rtmp_init.c').read_text().count('NdisZeroMemory(&pAd->'+field+',')==1

 result=json.loads(out.with_name(out.name+'.manifest.json').read_text())
 assert result['physical_stop_deferred_layer']['main_worker_hook']
 assert result['physical_stop_deferred_layer']['endpoint_installed']
 assert result['physical_stop_deferred_layer']['rebind_endpoint_installed']
 assert 'return wr_iot_physical_rebind_ioctl(ad,dev,rq);' in (out/'include/driver-api-closed-entry.inc').read_text()
 assert result['physical_stop_deferred_layer']['endpoint_scope']=='isolated no-host experiment only'
 assert (out/'include/wr-iot-peer-close-executor.inc').read_bytes()==(src/'include/wr-iot-peer-close-executor.inc').read_bytes()
 assert 'wr_iot_physical_stop_lifetime_capture_main(' in (out/'os/linux/rt_main_dev.c').read_text()
 assert '\n#include "physical-stop-arm-admission.inc"\n' in (out/'include/driver-api-closed-entry.inc').read_text()
 assert '#include "beacon-producer-gate.h"' not in (out/'include/physical-stop-prior-close.h').read_text()
 assert all(hashlib.sha256((out/n).read_bytes()).hexdigest()==h for n,h in result['merged_driver_sha256'].items())
 run(out,root/'duplicate',False);assert not (root/'duplicate').exists()
 (src/'os/linux/rt_main_dev.c').write_text('changed')
 run(src,root/'changed',False);assert not (root/'changed').exists()
print('PASS dormant deferred installer: exact manifest, immutable source/legacy executor, worker hook, refusal before output for drift/duplicate; full SDK/target pending')

print("PASS composed deferred-driver + initial storage preparation: storage-only worker unchanged; optional worker and WPIQ endpoint bound with exact manifest, guards/duplicate refused, source hashes and helper payloads preserved; reviewed SDK snippets, no target compile")
