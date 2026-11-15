"""PID-ref terminal acknowledgement after actual native CANCEL drops/lifetime end."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-publication.py')}
s=(here/'check-physical-initial-publication.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<publication fixture>','exec'),ns)
code=ns['code']
code=code.replace('#include "physical-initial-pins.inc"',r'''
#include "physical-initial-pins.inc"
struct pid {int value;};static struct pid first_pid={1},foreign_pid={2};
static struct pid *pid_identity=&first_pid;static int pid_refs=1;
static struct pid *task_pid(struct task_struct *t){assert(t==current);return pid_identity;}
static struct pid *get_pid(struct pid *p){assert(!locked);pid_refs++;return p;}
static void put_pid(struct pid *p){assert(p==&first_pid&&!locked&&pid_refs>1);pid_refs--;}
#include "physical-initial-terminal.inc"
''',1)
needle=' terminal.attempt=published;'
code=code.replace(needle,needle+r'''
 struct wr_iot_physical_initial_terminal cached={0};
 assert(wr_iot_physical_initial_terminal_prepare(&cached,&terminal)&&pid_refs==2);
 assert(wr_iot_physical_initial_terminal_matches(&cached,&terminal));
 assert(!wr_iot_physical_initial_terminal_prepare(&cached,&terminal)&&pid_refs==2);
 {struct wr_iot_physical_initial_request foreign=terminal;foreign.attempt++;
  assert(!wr_iot_physical_initial_terminal_matches(&cached,&foreign));
  foreign=terminal;foreign.action=WR_STOP_RELEASE;
  assert(!wr_iot_physical_initial_terminal_matches(&cached,&foreign));}
 pid_identity=&foreign_pid;
 assert(!wr_iot_physical_initial_terminal_matches(&cached,&terminal));
 pid_identity=&first_pid;
 assert(!cached.ready&&pid_refs==2);

 assert(!wr_iot_physical_initial_terminal_reply(&cached,&terminal,wire,64));
 assert(!wr_iot_physical_initial_terminal_commit(&cached,&arm_ad.wr_iot_physical_initial,
  &arm_ad.wr_iot_physical_lifetime,&arm_ad.wr_iot_physical_pins,&detached));
''',1)
needle=' assert(modules==1&&tasks==1&&devices==1);\n /* Lifetime and terminal reply are deliberately not acknowledged here. */'
replace=r'''
 assert(modules==1&&tasks==1&&devices==1);
 assert(!wr_iot_physical_initial_terminal_commit(&cached,&arm_ad.wr_iot_physical_initial,
  &arm_ad.wr_iot_physical_lifetime,&arm_ad.wr_iot_physical_pins,&detached));
 assert(wr_iot_physical_stop_lifetime_end(&arm_ad.wr_iot_physical_lifetime,
  arm_ad.wr_iot_physical_lifetime.serial,!arm_ad.wr_iot_physical_initial.task,
  !arm_ad.wr_iot_physical_pins.module&&!detached.module));
 for(unsigned fault=0;fault<8;fault++){
  struct wr_iot_physical_initial_terminal c=cached;
  struct wr_iot_physical_initial_record r=arm_ad.wr_iot_physical_initial;
  struct wr_iot_physical_stop_lifetime l=arm_ad.wr_iot_physical_lifetime;
  struct wr_iot_physical_stop_pins slot=arm_ad.wr_iot_physical_pins,local=detached;
  switch(fault){case 0:l.active=1;break;case 1:l.main_open_token=1;break;
   case 2:slot.module=1;break;case 3:local.task=current;break;
   case 4:r.origin.lifetime_serial=0;break;case 5:r.serial++;break;
   case 6:r.origin.main_device=NULL;break;case 7:c.status=WR_STOP_RELEASED;break;}
  assert(!wr_iot_physical_initial_terminal_commit(&c,&r,&l,&slot,&local));
  assert(!c.ready&&pid_refs==2);
 }
 assert(wr_iot_physical_initial_terminal_commit(&cached,&arm_ad.wr_iot_physical_initial,
  &arm_ad.wr_iot_physical_lifetime,&arm_ad.wr_iot_physical_pins,&detached));
 assert(!wr_iot_physical_initial_terminal_commit(&cached,&arm_ad.wr_iot_physical_initial,
  &arm_ad.wr_iot_physical_lifetime,&arm_ad.wr_iot_physical_pins,&detached));
 for(unsigned i=0;i<3;i++)assert(wr_iot_physical_initial_terminal_reply(&cached,&terminal,wire,64));
 assert(wr_iot_physical_initial_decode(&response,wire,64,1)&&response.status==WR_STOP_CANCELLED);
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
 pid_identity=&foreign_pid;assert(!wr_iot_physical_initial_terminal_reply(&cached,&terminal,wire,64));
 pid_identity=&first_pid;terminal.nonce[15]++;
 assert(!wr_iot_physical_initial_terminal_reply(&cached,&terminal,wire,64));
 assert(wr_iot_physical_initial_terminal_clear(&cached)&&pid_refs==1);
 assert(!wr_iot_physical_initial_terminal_clear(&cached));
'''
assert needle in code;code=code.replace(needle,replace,1)
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
print('PASS initial terminal PID-ref cache: no reply before native refs returned/lifetime end, commit once, repeated exact reply no puts, foreign PID/nonce refusal and PID release once; kernel ref primitives injected')
