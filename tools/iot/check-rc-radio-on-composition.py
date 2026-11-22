"""Actual RC ppoll priority/retirement, stable ON root boundary actor."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code='#define WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ON_OWNER\n'+(here/'check-rc-runtime.c').read_text()
code=code.replace('static volatile int notification,alarm_flag;',r'''
static int on_owned,on_steps,on_done,on_retire_allowed,on_retires,redispatches;
#ifdef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ON_OWNER
int wr_iot_radio_on_off_ready(void){return 0;}
#endif
int wr_iot_radio_on_pending(void){return on_owned;}
int wr_iot_radio_on_step(void){on_steps++;return on_done;}
int wr_iot_radio_on_retire(void){on_retires++;if(!on_retire_allowed)return 0;on_owned=0;wr_iot_rc_shutdown.radio_on_owned=0;return 1;}
static volatile int notification,alarm_flag;
''')
code=code.replace('int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner*s,const struct wr_iot_control_request*r){(void)s;(void)r;return 0;}', 'static int off_begins;\nint wr_iot_radio_off_begin(struct wr_iot_radio_off_owner*s,const struct wr_iot_control_request*r){(void)s;(void)r;off_begins++;return 0;}')
code=code.replace('int wr_iot_rc_dispatch(void){assert(0);return 0;}','int wr_iot_rc_dispatch(void){assert(!on_owned&&!wr_iot_rc_shutdown.radio_on_owned);redispatches++;return 0;}')
anchor=' assert(wr_iot_status_endpoint_close(&endpoint));'
assert code.count(anchor)==1
code=code.replace(anchor,r'''
 int old_steps=steps,old_physical=physical_steps,old_resume=resume_steps;
 on_owned=1;wr_iot_rc_shutdown.radio_on_owned=1;pending=physical_pending=resume_pending=1;
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=10};
 assert(!wr_iot_rc_radio_off_begin(&off,0)&&!off_begins);
 radio_off_redispatch=1;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(on_steps==1&&steps==old_steps&&physical_steps==old_physical&&resume_steps==old_resume&&!redispatches);
 on_done=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(on_steps==2&&on_retires==1&&on_owned&&!redispatches);
 on_retire_allowed=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(on_steps==3&&on_retires==2&&!on_owned&&!wr_iot_rc_shutdown.radio_on_owned&&radio_off_redispatch&&!redispatches);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(redispatches==1&&!radio_off_redispatch&&on_steps==3&&physical_steps==old_physical);
 pending=physical_pending=resume_pending=0;
'''+anchor)
with tempfile.TemporaryDirectory(prefix='wr-rc-on-compose-') as d:
    p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
    subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
    subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual RC ON ppoll composition: ON priority over redispatch/physical/resume/ordinary, one phase per cadence, failed retirement retains exclusion, successful retire then one later redispatch; root boundary actor, no public entry')
