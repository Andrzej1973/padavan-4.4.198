"""Execute actual read-only initial QUERY alongside real completion fixture."""
from pathlib import Path
import subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-terminal.py')}
s=(here/'check-physical-initial-terminal.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<completion fixture>','exec'),ns)
code=ns['code']
code=code.replace('struct wr_iot_physical_stop_pins wr_iot_physical_pending_pins;', 'struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;\n struct wr_iot_physical_initial_terminal wr_iot_physical_initial_terminal;\n struct wr_iot_physical_stop_pins wr_iot_physical_pending_pins;')
code=code.replace('#include "physical-stop-record.h"','#include "physical-stop-record.h"\n#include "physical-stop-terminal-types.h"\n#include "physical-initial-terminal-types.h"')
code=code.replace('#include "physical-initial-main-completion.inc"', '#include "physical-initial-main-completion.inc"\n#include "physical-initial-query.inc"\n#include "physical-initial-arm-admission.inc"\n#include "physical-initial-arm-abort.inc"\n#include "physical-initial-cleanup.inc"\n#include "physical-initial-terminal-replace.inc"\n#include "physical-initial-handler.inc"')
needle=' fail_module=1;'
test=r''' {
 RTMP_ADAPTER full=arm_ad;unsigned char output[64];
 struct wr_iot_physical_initial_request q=request;
 struct wr_iot_physical_initial_response decoded;
 memset(&full.wr_iot_physical_lifetime,0,sizeof(full.wr_iot_physical_lifetime));
 fail_module=1;
 assert(wr_iot_physical_initial_handle(&full,&main_dev,&q,output,64)==-ENOMEM);
 assert(!full.wr_iot_physical_lifetime.active&&modules==1&&tasks==1&&devices==1);
 fail_module=0;
 assert(!wr_iot_physical_initial_handle(&full,&main_dev,&q,output,64));
 assert(wr_iot_physical_initial_decode(&decoded,output,64,1));
 assert(decoded.status==WR_STOP_ARMED&&modules==2&&tasks==2&&devices==2);
 for(unsigned retry=0;retry<3;retry++)
  assert(!wr_iot_physical_initial_handle(&full,&main_dev,&q,output,64));
 assert(full.wr_iot_physical_initial.serial==1&&modules==2&&tasks==2&&devices==2);
 q.action=WR_STOP_QUERY;q.attempt=1;
 assert(!wr_iot_physical_initial_handle(&full,&main_dev,&q,output,64));
 q.action=WR_STOP_CANCEL;
 {struct wr_iot_physical_initial_request foreign=q;foreign.nonce[0]^=1;
  assert(wr_iot_physical_initial_handle(&full,&main_dev,&foreign,output,64)==-EAGAIN);
  assert(!full.wr_iot_physical_initial_terminal.owner&&pid_refs==1);}
 assert(!wr_iot_physical_initial_handle(&full,&main_dev,&q,output,64));
 assert(wr_iot_physical_initial_decode(&decoded,output,64,1)&&decoded.status==WR_STOP_CANCELLED);
 for(unsigned retry=0;retry<3;retry++)
  assert(!wr_iot_physical_initial_handle(&full,&main_dev,&q,output,64));
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2&&!full.wr_iot_physical_lifetime.active);
 assert(wr_iot_physical_initial_terminal_clear(&full.wr_iot_physical_initial_terminal));
 assert(pid_refs==1&&!locked);
 }
'''
assert code.count(needle)==1;code=code.replace(needle,test+needle)
old=''' ad.wr_iot_physical_pins.module=1;ad.wr_iot_physical_pins.task=(struct task_struct *)&task;
 ad.wr_iot_physical_pins.device=(struct net_device *)&main_dev;'''
assert old in code
code=code.replace(old,''' assert(wr_iot_physical_stop_pins_acquire(&ad.wr_iot_physical_pins,current,(struct net_device *)&main_dev));''',1)
release=r''' {
 struct wr_iot_physical_initial_request q=ad.wr_iot_physical_initial.request;
 unsigned char output[64];
 ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;
 q.action=WR_STOP_RELEASE;q.attempt=ad.wr_iot_physical_initial.serial;
 assert(!wr_iot_physical_initial_handle(&ad,&main_dev,&q,output,64));
 for(unsigned retry=0;retry<3;retry++)
  assert(!wr_iot_physical_initial_handle(&ad,&main_dev,&q,output,64));
 assert(output[6]==WR_STOP_RELEASED&&modules==1&&tasks==1&&devices==1&&pid_refs==2);
 assert(!ad.wr_iot_physical_lifetime.active&&!ad.wr_iot_physical_initial.task);
 assert(wr_iot_physical_initial_terminal_clear(&ad.wr_iot_physical_initial_terminal));
 assert(pid_refs==1);
 }
'''
anchor=' ad.wr_iot_transition.epoch++;'
assert code.count(anchor)==1;code=code.replace(anchor,release+anchor)

with tempfile.TemporaryDirectory(prefix='wr-initial-query-') as d:
 root=Path(d)
 for p in here.glob('*.h'):shutil.copy2(p,root/p.name)
 for name in ('radio-transition.h','radio-transition-api.h'):
  p=root/name;p.write_text(p.read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 unit=root/'check.c';unit.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual initial transaction provider: failed pin acquisition unwinds, ARM/retry/query/CANCEL/retry returns refs once; foreign terminal cannot occupy cache; exact Main COMPLETE/RELEASE/retry returns refs once; ioctl uninstalled')
