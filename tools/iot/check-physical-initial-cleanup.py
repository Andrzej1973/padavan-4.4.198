"""Actual persistent initial cleanup wrapper; native ref primitives injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-terminal.py')}
s=(here/'check-physical-initial-terminal.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<terminal fixture>','exec'),ns)
code=ns['code'].replace('#include "physical-initial-main-completion.inc"','#include "physical-initial-main-completion.inc"\n#include "physical-initial-cleanup.inc"',1)
code=code.replace('#include "physical-initial-cleanup.inc"',r'''
static RTMP_ADAPTER *cancel_fault;
static unsigned cancel_drops;
static int cancel_observed_drop(struct wr_iot_physical_stop_pins *p){
 int result=wr_iot_physical_stop_pins_drop(p);cancel_drops++;
 if(result&&cancel_fault)cancel_fault->wr_iot_transition.active_tx=1;
 return result;
}
#define wr_iot_physical_stop_pins_drop cancel_observed_drop
#include "physical-initial-cleanup.inc"
#undef wr_iot_physical_stop_pins_drop
''',1)
a=code.index(' struct wr_iot_physical_initial_terminal cached={0};')
b=code.index(' assert(!wr_iot_physical_initial_terminal_clear(&cached));',a)+len(' assert(!wr_iot_physical_initial_terminal_clear(&cached));')
code=code[:a]+r'''
 (void)foreign_pid;
 struct wr_iot_physical_initial_terminal cached={0};
 arm_ad.wr_iot_transition.active_tx=1;
 assert(wr_iot_physical_initial_cleanup(&arm_ad,&main_dev,&terminal,&cached)==-EAGAIN);
 assert(cached.owner&&cached.cleanup_phase==0&&modules==2&&tasks==2&&devices==2);
 struct wr_iot_physical_initial_request foreign=terminal;foreign.attempt++;
 assert(wr_iot_physical_initial_cleanup(&arm_ad,&main_dev,&foreign,&cached)==-EBUSY);
 assert(pid_refs==2);
 arm_ad.wr_iot_transition.active_tx=0;cancel_fault=&arm_ad;
 assert(wr_iot_physical_initial_cleanup(&arm_ad,&main_dev,&terminal,&cached)==-EAGAIN);
 assert(cached.cleanup_phase==2&&!cached.ready&&cancel_drops==1);
 assert(modules==1&&tasks==1&&devices==1&&arm_ad.wr_iot_physical_lifetime.active);
 assert(!wr_iot_physical_initial_terminal_reply(&cached,&terminal,wire,64));
 assert(wr_iot_physical_initial_cleanup(&arm_ad,&main_dev,&terminal,&cached)==-EAGAIN);
 assert(cancel_drops==1&&cached.cleanup_phase==2);
 cancel_fault=NULL;arm_ad.wr_iot_transition.active_tx=0;
 assert(!wr_iot_physical_initial_cleanup(&arm_ad,&main_dev,&terminal,&cached));
 assert(cancel_drops==1);
 assert(cached.ready&&cached.cleanup_phase==3&&!arm_ad.wr_iot_physical_lifetime.active);
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
 for(unsigned repeat=0;repeat<3;repeat++){
  assert(!wr_iot_physical_initial_cleanup(&arm_ad,&main_dev,&terminal,&cached));
  assert(wr_iot_physical_initial_terminal_reply(&cached,&terminal,wire,64));
 }
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
 assert(wr_iot_physical_initial_terminal_clear(&cached)&&pid_refs==1);
'''+code[b:]

with tempfile.TemporaryDirectory(prefix='wr-initial-terminal-') as d:
 root=Path(d)
 for p in here.glob('*.h'):
  text=p.read_text()
  if p.name in ('radio-transition.h','radio-transition-api.h'):
   text=text.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (root/p.name).write_text(text)
 unit=root/'check.c';unit.write_text(code);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual initial cleanup wrapper CANCEL: retained preflight refusal, foreign retry refusal, native detach/drop/lifetime end/commit, exact repeated reply no extra puts; endpoint uninstalled')
