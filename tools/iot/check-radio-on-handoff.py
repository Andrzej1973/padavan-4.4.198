"""Actual prepared restore to one retained rebind submission, with backend actor."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-restore.py').read_text()
ns={'__file__':str(here/'check-radio-on-restore.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-handoff.h"
static int begins,continues,admitted,active;
int wr_iot_rc_rebind_begin(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p){assert(r->created==10&&!strcmp(r->id,"01000000000000000000000000000000")&&p->epoch==1&&p->generation==2);begins++;return admitted;}
enum wr_iot_result_state wr_iot_activation_continue(const char*id,unsigned long long created){assert(created==10&&!strcmp(id,"01000000000000000000000000000000"));continues++;return WR_IOT_RESULT_APPLIED;}
int wr_iot_rc_rebind_active_current(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){assert(r->created==10&&!strcmp(r->request.ssid,"IoT")&&p->action==WR_STOP_RELEASE);return active&&i->adapter_epoch==2&&i->device_generation==2;}
#include "radio-on-handoff.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int accepted=0;accepted<2;accepted++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_restore restore={0};unsigned char id[16]={1};
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;bridge_fail=no_submit=0;
  ram_calls=mc_calls=service_calls=0;ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&restore,&a,&desired,1,id));
  int ready=0;for(int tick=0;tick<30&&!ready;tick++)ready=wr_iot_on_restore_step(&restore);assert(ready);
  struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10,.request=desired},wrong;
  begins=continues=active=0;admitted=accepted;
  wrong=request;wrong.id[0]='2';assert(!wr_iot_on_restore_handoff(&restore,&wrong)&&!begins);
#define WRONG(f) wrong=request;strcpy(wrong.request.f,"foreign");assert(!wr_iot_on_restore_handoff(&restore,&wrong)&&!begins);
  WRONG(ssid) WRONG(password) WRONG(gateway) WRONG(mask) WRONG(first) WRONG(last)
#undef WRONG
  wrong=request;wrong.created=0;assert(!wr_iot_on_restore_handoff(&restore,&wrong)&&!begins);
  assert(wr_iot_on_restore_handoff(&restore,&request)==accepted&&begins==1&&restore.phase==WR_ON_RESTORE_HANDOFF);
  assert(!wr_iot_on_restore_handoff(&restore,&request)&&begins==1);
  assert(!wr_iot_on_rebind_step(&restore)&&continues==1); /* APPLIED is insufficient. */
  assert(!wr_iot_on_rebind_current(&restore)&&continues==1);
  active=1;assert(wr_iot_on_rebind_current(&restore)&&continues==1);
  assert(wr_iot_on_rebind_step(&restore)&&continues==2);
  restore.main.identity.adapter_epoch=3;assert(!wr_iot_on_rebind_step(&restore));restore.main.identity.adapter_epoch=2;
  receipt.attempt++;int prior=continues;assert(!wr_iot_on_rebind_step(&restore)&&continues==prior);receipt.attempt--;
  aux_ok=0;assert(!wr_iot_on_rebind_step(&restore)&&continues==prior);aux_ok=1;
  mc_read=0;assert(!wr_iot_on_rebind_step(&restore));mc_read=1;
  assert(wr_iot_on_rebind_step(&restore)&&begins==1&&ups==1&&generator_calls==1&&a.profile.active&&a.busy);
  wr_iot_bundle_release(&a.profile.files);memset(&a.profile,0,sizeof(a.profile));a.busy=0;
  assert(wr_iot_on_admission_cancel(&a)&&!depth);assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-handoff-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON handoff actual restore composition: exact nonce/six fields/time, begin once even refusal, exact continuation, APPLIED alone refused, active epoch/receipt/AUX/multicast proof, retained baseline; backend actor, no driver/runtime acceptance')
