"""RC wait gives retained owners priority, then dispatches boot publication later."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code='#define WR_IOT_RUNTIME_FIXTURE_EXTERNAL_BOOT\n'+(here/'check-rc-runtime.c').read_text()
a='static volatile int notification,alarm_flag;'
b=r'''
static int boot_pending,boot_steps,dispatches;
int wr_iot_rc_boot_pending(void){return boot_pending;}
int wr_iot_rc_boot_step(void){boot_steps++;boot_pending=0;return 1;}
static volatile int notification,alarm_flag;
''';assert code.count(a)==1;code=code.replace(a,b)
a='int wr_iot_rc_dispatch(void){assert(0);return 0;}';assert code.count(a)==1;code=code.replace(a,'int wr_iot_rc_dispatch(void){assert(!boot_pending);dispatches++;return 0;}')
a=' assert(wr_iot_status_endpoint_close(&endpoint));'
b=r'''
 boot_pending=pending=1;int old_steps=steps;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(steps==old_steps+1&&!boot_steps&&!dispatches&&boot_pending);
 pending=0;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(boot_steps==1&&!boot_pending&&radio_off_redispatch&&!dispatches);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(dispatches==1&&!radio_off_redispatch&&boot_steps==1);
'''+a;assert code.count(a)==1;code=code.replace(a,b)
with tempfile.TemporaryDirectory(prefix='wr-rc-boot-schedule-') as d:
 p=Path(d)/'check.c';p.write_text(code);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=20)
print('PASS actual RC boot scheduling: retained normal continuation wins, one boot step per cadence, successful publication dispatched exactly once on later tick; boot boundary actor, real mailbox/status wait regressions')
