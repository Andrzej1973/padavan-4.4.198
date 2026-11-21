from pathlib import Path
import subprocess,tempfile,json,datetime,hashlib
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-handler.py')};s=(here/'check-physical-initial-handler.py').read_text();exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<provider fixture>','exec'),ns)
code=ns['code']
a=' assert(wr_iot_physical_initial_terminal_clear(&full.wr_iot_physical_initial_terminal));'
b=r'''
 {struct wr_iot_physical_initial_request fresh=request;fresh.nonce[0]^=2;
  struct wr_iot_physical_initial_request old_cancel=q;
  assert(wr_iot_physical_initial_handle(&full,&main_dev,&request,output,64)==-EBUSY);
  pid_identity=&foreign_pid;
  assert(wr_iot_physical_initial_handle(&full,&main_dev,&fresh,output,64)==-EBUSY);
  pid_identity=&first_pid;
  full.wr_iot_control_users=1;
  assert(wr_iot_physical_initial_handle(&full,&main_dev,&fresh,output,64)==-EAGAIN);
  assert(full.wr_iot_physical_initial.serial==1&&pid_refs==2);
  assert(!wr_iot_physical_initial_handle(&full,&main_dev,&old_cancel,output,64));
  full.wr_iot_control_users=0;
  {int result=wr_iot_physical_initial_handle(&full,&main_dev,&fresh,output,64);
   assert(!result);}
  assert(full.wr_iot_physical_initial.serial==2&&pid_refs==1&&modules==2&&tasks==2&&devices==2);
  assert(wr_iot_physical_initial_handle(&full,&main_dev,&old_cancel,output,64)==-EAGAIN);
  fresh.action=WR_STOP_CANCEL;fresh.attempt=2;
  assert(!wr_iot_physical_initial_handle(&full,&main_dev,&fresh,output,64));
  assert(modules==1&&tasks==1&&devices==1&&pid_refs==2);
 }
'''+a
assert code.count(a)==1;code=code.replace(a,b)
release_anchor=' assert(wr_iot_physical_initial_terminal_clear(&ad.wr_iot_physical_initial_terminal));'
release_check=r''' {struct wr_iot_physical_initial_request fresh=request;fresh.action=WR_STOP_ARM;fresh.attempt=0;fresh.nonce[0]^=2;
  assert(wr_iot_physical_initial_handle(&ad,&main_dev,&fresh,output,64)==-EBUSY);
  assert(ad.wr_iot_physical_initial_terminal.ready&&pid_refs==2);
 }
'''
assert code.count(release_anchor)==1;code=code.replace(release_anchor,release_check+release_anchor)

with tempfile.TemporaryDirectory(prefix='wr-rearm-prototype-') as d:
 root=Path(d)
 for p in here.glob('*.h'):
  text=p.read_text()
  if p.name in ('radio-transition.h','radio-transition-api.h'):text=text.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (root/p.name).write_text(text)
 (root/'check.c').write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),d+'/check.c','-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual CANCEL rearm: exact fresh ARM advances attempt, failed admission restores old reply, same nonce/foreign PID/stale CANCEL/RELEASE refuse, refs returned once; target unverified')
