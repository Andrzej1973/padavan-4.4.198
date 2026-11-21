"""Disabled idle proof with actual release/WAN/terminal IAPP composition."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-followup.py')}
exec((here/'check-radio-on-followup.py').read_text().split('for gate in (0,1):',1)[0],ns)
body=ns['body']
actors=r'''
#include "radio-on-disabled.h"
int wr_iot_initial_off_begin(struct wr_iot_initial_off*s,const struct wr_iot_control_request*r){assert(!r->request.enabled);s->owner=getpid();s->ready=1;s->idle.epoch=2;s->idle.generation=2;return 1;}
int wr_iot_initial_off_restarted_observed(const struct wr_iot_initial_off*s,const struct wr_iot_physical_stop_request*r,const struct wr_iot_driver_identity*m){assert(s->ready&&r->action==WR_STOP_RELEASE&&m->adapter_epoch==2);return network_current;}
int wr_iot_initial_off_observed(const struct wr_iot_initial_off*s){assert(depth&&s->ready);return network_current;}
#include "radio-on-disabled.c"
'''
body=body.replace('int main(int argc',actors+'\nint main(int argc',1)
body=body.replace('struct wr_iot_on_admission a={0};','struct wr_iot_request off={0};struct wr_iot_on_disabled witness={0};struct wr_iot_on_admission a={0};')
body=body.replace('wr_iot_on_restore_begin(&restore,&a,&desired,1,id)','wr_iot_on_restore_begin(&restore,&a,&off,1,id)')
body=body.replace('admitted=active=1;begins=continues=0;assert(wr_iot_on_restore_handoff(&restore,&request));','request.request=off;assert(wr_iot_on_disabled_begin(&witness,&restore,&request));')
body=body.replace('wr_iot_rc_radio_on_release(&restore)','wr_iot_on_disabled_release(&witness)').replace('wr_iot_on_followup_step(&restore)','wr_iot_on_disabled_followup(&witness)')
for gate in (0,1):
 with tempfile.TemporaryDirectory(prefix='wr-on-disabled-followup-') as d:
  root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
  p=root/'check.c';p.write_text(f'#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED {gate}\n'+body);b=root/'check'
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b),d],check=True,timeout=15)
print('PASS disabled restore/release/WAN/IAPP: fresh idle and parent loss hold; one WAN/LED/child, unknown drains, failed child retained, DONE rechecks idle/profile, gate0 inert; SDK actors')
