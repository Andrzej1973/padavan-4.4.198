"""Actual RC wait loop cold-root cadence/retirement and cancellation boundary."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-rc-radio-on-composition.py')}
source=(here/'check-rc-radio-on-composition.py').read_text()
exec(source.split('with tempfile.TemporaryDirectory(',1)[0],ns)
code=ns['code'].replace('WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ON_OWNER','WR_IOT_RUNTIME_FIXTURE_EXTERNAL_COLD_OWNER')
code=code.replace('wr_iot_radio_on_pending','wr_iot_cold_on_pending').replace('wr_iot_radio_on_step','wr_iot_cold_on_step').replace('wr_iot_radio_on_retire','wr_iot_cold_on_retire')
code=code.replace('static volatile int notification,alarm_flag;',
 'int wr_iot_radio_on_pending(void){return 0;}\nint wr_iot_radio_on_step(void){assert(0);return 0;}\nint wr_iot_radio_on_retire(void){assert(0);return 0;}\nstatic volatile int notification,alarm_flag;')
a='int wr_iot_cold_on_step(void){on_steps++;return on_done;}'
b='int wr_iot_cold_on_step(void){on_steps++;if(on_done==-1){on_owned=0;wr_iot_rc_shutdown.radio_on_owned=0;}return on_done;}'
assert code.count(a)==1;code=code.replace(a,b)
a=' pending=physical_pending=resume_pending=0;'
b=r'''
 /* Checked cancellation must not redispatch the cancelled startup as success. */
 on_owned=1;on_done=-1;wr_iot_rc_shutdown.radio_on_owned=1;
 int before_dispatch=redispatches,before_retire=on_retires;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(!on_owned&&!wr_iot_rc_shutdown.radio_on_owned&&!radio_off_redispatch&&
        redispatches==before_dispatch&&on_retires==before_retire);
'''+a
assert code.count(a)==1;code=code.replace(a,b)
with tempfile.TemporaryDirectory(prefix='wr-rc-cold-compose-') as d:
 p=Path(d)/'check.c';p.write_text(code);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=20)
print('PASS actual RC cold slot scheduling: one continuation per cadence, exclusion blocks OFF, failed retire retains, one later redispatch after checked success, cancellation neither retires nor redispatches; root actor, stock entry unbound')
