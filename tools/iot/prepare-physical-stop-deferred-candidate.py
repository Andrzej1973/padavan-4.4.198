#!/usr/bin/env python3
"""Stage dormant ARM storage and actual deferred Main hook in an isolated copy.

No endpoint or ACK/DMA policy changes; not production or runtime acceptance.
"""
import argparse,hashlib,json,runpy,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
if any(f.is_symlink() for f in src.rglob('*')):p.error('symlink input refused')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text())
hashes=lambda root:{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or hashes(src)!=m.get('merged_driver_sha256') or 'main_physical_close_delegation_layer' not in m or 'ra2_no_host_experiment' not in m:
 p.error('intact delegated candidate required')
here=Path(__file__).resolve().parent
helpers=runpy.run_path(str(here/'physical-stop-executor.py'))
main=runpy.run_path(str(here/'physical-stop-main-binding.py'))
paths=('include/rtmp.h','common/rtmp_init.c','os/linux/rt_main_dev.c',
 'include/wr-iot-peer-open-dispatch.inc','include/wr-iot-mbss-recovery-work.inc',
 'include/wr-iot-mbss-recovery-join.inc','include/wr-iot-reset-admission.inc','include/driver-api-closed-entry.inc','include/wr-iot-raw-recovery-free-fence.inc')
texts={n:(src/n).read_text() for n in paths}
try:
 texts[paths[0]],texts[paths[1]]=helpers['compose_adapter'](texts[paths[0]],texts[paths[1]])
 texts[paths[2]]=main['compose'](texts[paths[2]])
 texts[paths[6]]=main['compose_reset'](texts[paths[6]])
 texts[paths[8]]=main['compose_raw_free'](texts[paths[8]])
 if texts[paths[7]].count('#define WR_IOT_RA2_NO_HOST_MODE 1')!=1:
  raise ValueError('verified no-host dispatch definition required')
 texts[paths[7]]+='\n#include "physical-stop-arm-admission.inc"\n#include "physical-stop-pins.inc"\n#include "physical-stop-arm-publication.inc"\n#include "physical-stop-main-completion.inc"\n#include "physical-stop-terminal.inc"\n#include "physical-stop-cancel.inc"\n#include "physical-stop-terminal-replace.inc"\n#include "physical-stop-release.inc"\n#include "physical-stop-query.inc"\n'
 texts[paths[3]]=helpers['compose_open_dispatch'](texts[paths[3]])
 texts[paths[4]],texts[paths[5]]=helpers['compose_retirement'](texts[paths[4]],texts[paths[5]])
except ValueError as e:p.error(str(e))
for n in ('physical-stop-record.h','physical-stop-lifetime.h','physical-stop-pin-types.h','physical-stop-terminal-types.h','physical-stop-prior-close.h','physical-stop-wire.h','physical-stop-arm-admission.inc','physical-stop-pins.inc','physical-stop-arm-publication.inc','physical-stop-main-completion.inc','physical-stop-terminal.inc','physical-stop-response.h','physical-stop-cancel.inc','physical-stop-terminal-replace.inc','physical-stop-release.inc','physical-stop-query.inc'):
 if (src/'include'/n).exists():p.error('already staged '+n)
shutil.copytree(src,out)
for n,text in texts.items():(out/n).write_text(text)
for n in ('physical-stop-record.h','physical-stop-lifetime.h','physical-stop-pin-types.h','physical-stop-terminal-types.h','physical-stop-prior-close.h','physical-stop-wire.h','physical-stop-arm-admission.inc','physical-stop-pins.inc','physical-stop-arm-publication.inc','physical-stop-main-completion.inc','physical-stop-terminal.inc','physical-stop-response.h','physical-stop-cancel.inc','physical-stop-terminal-replace.inc','physical-stop-release.inc','physical-stop-query.inc'):
 (out/'include'/n).write_text((here/n).read_text().replace('#include "beacon-producer-gate.h"', '#include "wr-iot-beacon-producer-gate.h"'))
m['merged_driver_sha256']=hashes(out)
if 'candidate_driver_sha256' in m:
 for n in paths:m['candidate_driver_sha256'][n]=m['merged_driver_sha256'][n]
 for n in ('physical-stop-record.h','physical-stop-lifetime.h','physical-stop-pin-types.h','physical-stop-terminal-types.h','physical-stop-prior-close.h','physical-stop-wire.h','physical-stop-arm-admission.inc','physical-stop-pins.inc','physical-stop-arm-publication.inc','physical-stop-main-completion.inc','physical-stop-terminal.inc','physical-stop-response.h','physical-stop-cancel.inc','physical-stop-terminal-replace.inc','physical-stop-release.inc','physical-stop-query.inc'):
  m['candidate_driver_sha256']['include/'+n]=m['merged_driver_sha256']['include/'+n]
m['physical_stop_deferred_layer']={'dormant':True,'main_worker_hook':True,
 'legacy_executor_modified':False,'endpoint_installed':False,'arm_admission_source_staged':True,
 'reset_arm_gate_staged':True,'reset_admission_complete':False,'target_compiled':False,'runtime_verified':False}
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('PASS staged dormant deferred Main ARM hook/storage; endpoint/reset/physical completion unbound')
