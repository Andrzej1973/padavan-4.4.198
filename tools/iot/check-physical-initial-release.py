"""Actual checked Main completion, native RELEASE refs and PID terminal replay."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-terminal.py')}
s=(here/'check-physical-initial-terminal.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<terminal fixture>','exec'),ns)
code=ns['code']
old=''' ad.wr_iot_physical_pins.module=1;ad.wr_iot_physical_pins.task=(struct task_struct *)&task;
 ad.wr_iot_physical_pins.device=(struct net_device *)&main_dev;'''
assert old in code
code=code.replace(old,''' assert(wr_iot_physical_stop_pins_acquire(&ad.wr_iot_physical_pins,current,(struct net_device *)&main_dev));
 assert(modules==2&&tasks==2&&devices==2);''',1)
needle=' ad.wr_iot_transition.epoch++;'
body=r'''
 struct wr_iot_physical_initial_request release_request=ad.wr_iot_physical_initial.request;
 release_request.action=WR_STOP_RELEASE;release_request.attempt=ad.wr_iot_physical_initial.serial;
 struct wr_iot_physical_initial_terminal released_cache={0};
 struct wr_iot_physical_stop_pins release_local={0};
 assert(wr_iot_physical_initial_terminal_prepare(&released_cache,&release_request));
 assert(!wr_iot_physical_initial_terminal_commit(&released_cache,&ad.wr_iot_physical_initial,
  &ad.wr_iot_physical_lifetime,&ad.wr_iot_physical_pins,&release_local));
 ad.wr_iot_physical_initial.status=WR_STOP_RUNNING;
 assert(!wr_iot_physical_initial_pins_detach(&ad.wr_iot_physical_pins,&release_local,&ad.wr_iot_physical_initial,&release_request));
 ad.wr_iot_physical_initial.status=WR_STOP_COMPLETE;
 locked=1;
 assert(wr_iot_physical_initial_pins_detach(&ad.wr_iot_physical_pins,&release_local,&ad.wr_iot_physical_initial,&release_request));
 locked=0;
 assert(modules==2&&tasks==2&&devices==2);
 assert(!wr_iot_physical_initial_terminal_commit(&released_cache,&ad.wr_iot_physical_initial,
  &ad.wr_iot_physical_lifetime,&ad.wr_iot_physical_pins,&release_local));
 assert(wr_iot_physical_stop_pins_drop(&release_local));
 assert(modules==1&&tasks==1&&devices==1);
 assert(!wr_iot_physical_initial_terminal_commit(&released_cache,&ad.wr_iot_physical_initial,
  &ad.wr_iot_physical_lifetime,&ad.wr_iot_physical_pins,&release_local));
 assert(wr_iot_physical_stop_lifetime_end(&ad.wr_iot_physical_lifetime,
  ad.wr_iot_physical_lifetime.serial,!ad.wr_iot_physical_initial.task,
  !ad.wr_iot_physical_pins.module&&!release_local.module));
 assert(wr_iot_physical_initial_terminal_commit(&released_cache,&ad.wr_iot_physical_initial,
  &ad.wr_iot_physical_lifetime,&ad.wr_iot_physical_pins,&release_local));
 for(unsigned repeat=0;repeat<3;repeat++){
  assert(wr_iot_physical_initial_terminal_reply(&released_cache,&release_request,wire,64));
  assert(wr_iot_physical_initial_decode(&response,wire,64,1)&&response.status==WR_STOP_RELEASED);
 }
 assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
 assert(wr_iot_physical_initial_terminal_clear(&released_cache)&&pid_refs==1);
'''
assert needle in code;code=code.replace(needle,body+needle,1)
with tempfile.TemporaryDirectory(prefix='wr-initial-release-') as d:
 root=Path(d)
 for p in here.glob('*.h'):
  text=p.read_text()
  if p.name in ('radio-transition.h','radio-transition-api.h'):
   text=text.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (root/p.name).write_text(text)
 unit=root/'check.c';unit.write_text(code);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS initial checked COMPLETE/native RELEASE/PID terminal composition: RUNNING refuses, detach no puts, drop outside locks once, reply only after lifetime end, repeated RELEASE no extra puts; kernel primitives injected')
