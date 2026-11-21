"""Actual initial ARM admission with reviewed live-probe fixture; host only."""
from pathlib import Path
import subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-publication.py')}
s=(here/'check-physical-initial-publication.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<publication fixture>','exec'),ns)
code=ns['code']
code=code.replace('struct wr_iot_physical_stop_pins wr_iot_physical_pending_pins;', 'struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;\n struct wr_iot_physical_initial_terminal wr_iot_physical_initial_terminal;\n struct wr_iot_physical_stop_pins wr_iot_physical_pending_pins;')
code=code.replace('#include "physical-stop-record.h"','#include "physical-stop-record.h"\n#include "physical-stop-terminal-types.h"\n#include "physical-initial-terminal-types.h"')
code=code.replace('#include "physical-initial-arm-publication.inc"','#include "physical-initial-arm-publication.inc"\n#include "physical-initial-arm-admission.inc"\n#include "physical-initial-arm-abort.inc"')
needle=' fail_module=1;'
test=r''' {
 RTMP_ADAPTER ready=arm_ad;unsigned long serial=99;
 /* Admission fixture begins before lifetime acquisition. Probe itself is real. */
 memset(&ready.wr_iot_physical_lifetime,0,sizeof(ready.wr_iot_physical_lifetime));
 for(unsigned fault=0;fault<8;fault++){
  RTMP_ADAPTER bad=ready;struct wr_iot_physical_initial_request q=request;
  switch(fault){case 0:q.epoch++;break;case 1:q.idle_serial++;break;
   case 2:bad.wr_iot_idle_probe.accepted=0;break;
   case 3:bad.wr_iot_physical_pins.module=1;break;
   case 4:bad.wr_iot_control_users=1;break;
   case 5:bad.wr_iot_peer_table_owner.transactions=1;break;
   case 6:bad.wr_iot_interface_refs[1].last_token=1;break;
   case 7:bad.wr_iot_physical_initial_terminal.owner=(struct pid *)&task;break;}
  serial=99;
  assert(wr_iot_physical_initial_arm_admit(&bad,&main_dev,&q,&serial)==-EAGAIN);
  assert(!serial&&!bad.wr_iot_physical_lifetime.active&&!locked);
 }
 assert(!wr_iot_physical_initial_arm_admit(&ready,&main_dev,&request,&serial));
 assert(serial&&ready.wr_iot_physical_lifetime.active);
 assert(!ready.wr_iot_physical_lifetime.arm_request.action);
 assert(wr_iot_physical_initial_arm_admit(&ready,&main_dev,&request,&serial)==-EAGAIN);
 assert(!serial&&ready.wr_iot_physical_lifetime.active);
 assert(modules==1&&tasks==1&&devices==1);
 {
 unsigned long acquired=ready.wr_iot_physical_lifetime.serial;
 for(unsigned fault=0;fault<5;fault++){
  RTMP_ADAPTER bad=ready;unsigned long wrong=acquired;
  switch(fault){case 0:wrong++;break;
   case 1:bad.wr_iot_physical_pending_pins.module=1;break;
   case 2:bad.wr_iot_physical_initial.task=&task;break;
   case 3:bad.wr_iot_physical_lifetime.main_ticket_valid=1;break;
   case 4:bad.wr_iot_transition.active_tx=1;break;}
  assert(wr_iot_physical_initial_arm_abort_unpublished(&bad,&main_dev,wrong)==-EAGAIN);
  assert(bad.wr_iot_physical_lifetime.active&&!locked);
 }
 assert(wr_iot_physical_stop_pins_acquire(&ready.wr_iot_physical_pending_pins,
   current,(struct net_device *)&main_dev));
 assert(wr_iot_physical_initial_arm_abort_unpublished(&ready,&main_dev,acquired)==-EAGAIN);
 assert(ready.wr_iot_physical_lifetime.active&&modules==2&&tasks==2&&devices==2);
 assert(wr_iot_physical_stop_pins_drop(&ready.wr_iot_physical_pending_pins));
 assert(modules==1&&tasks==1&&devices==1);
 assert(!wr_iot_physical_initial_arm_abort_unpublished(&ready,&main_dev,acquired));
 assert(!ready.wr_iot_physical_lifetime.active);
 assert(wr_iot_physical_initial_arm_abort_unpublished(&ready,&main_dev,acquired)==-EAGAIN);
 assert(!wr_iot_physical_initial_arm_admit(&ready,&main_dev,&request,&serial));
 assert(serial>acquired);
 }
 arm_ad=ready; /* Run inherited native pin acquisition/publication/cleanup below. */
 }
'''
assert code.count(needle)==1;code=code.replace(needle,test+needle)
with tempfile.TemporaryDirectory(prefix='wr-initial-admission-') as d:
 root=Path(d)
 for p in here.glob('*.h'):shutil.copy2(p,root/p.name)
 for name in ('radio-transition.h','radio-transition-api.h'):
  p=root/name;p.write_text(p.read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 unit=root/'check.c';unit.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual initial ARM admission: exact accepted probe acquires lifetime once; eight identity/owner/history faults retain inactive state; unpublished abort requires native pins returned, rejects captured Main ticket/stale serial, allows fresh admission; endpoint uninstalled')
