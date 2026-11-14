"""Actual physical admission/session/fence with real authentication controller."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
for line in ['int wr_iot_auth_stop_begin(struct wr_iot_auth_stop*s,unsigned long long now){assert(now);s->owner=getpid();return 1;}','int wr_iot_auth_stop_step(struct wr_iot_auth_stop*s,unsigned long long now){assert(s->owner==getpid()&&now);return 1;}']:
 assert code.count(line)==1;code=code.replace(line,'')
code+=r'''
static int auth_present=1,auth_signals;
int wr_iot_auth_stop_present(void){assert(depth==2&&!aux_calls&&!downs);return auth_present;}
int wr_iot_auth_stop_signal(int sig){assert(sig==SIGTERM&&depth==2&&!aux_calls&&!downs);auth_signals++;return 1;}
int main(void){
 (void)handler;struct wr_iot_rc_physical_intent intent={0};
 assert(wr_iot_rc_physical_begin(&intent));wr_iot_rc_physical_step();
 assert(auth_signals==1&&!aux_calls&&!downs&&!calls);
 wr_iot_rc_physical_step();assert(auth_signals==1&&!aux_calls&&!downs);
 auth_present=-1;wr_iot_rc_physical_step();assert(!aux_calls&&!downs);
 auth_present=0;wr_iot_rc_physical_step();assert(aux_calls==1&&!downs&&!calls);
 auth_present=1;wr_iot_rc_physical_step();assert(aux_calls==1&&!downs&&auth_signals==1);
 auth_present=0;wr_iot_rc_physical_step();assert(aux_calls==1&&!downs&&physical.auth.phase==WR_AUTH_RETAINED);
 /* Reappearing service cannot be killed again or bypassed. */
}
'''
# Presence observation is valid with already-completed AUX slots too.
code=code.replace('assert(depth==2&&!aux_calls&&!downs);return auth_present;','assert(depth==2&&!downs);return auth_present;')
with tempfile.TemporaryDirectory(prefix='wr-physical-auth-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-auth-stop.c'),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual physical/auth controller gate: TERM once before any AUX/Main/ARM, present/unknown retain, fresh absence admits first AUX; service/backend/driver actors injected')
