#!/usr/bin/env python3
"""Repeated physical resume through actual retained RC owner and OFF lifecycle."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-rebind-owner.py').read_text();ns={'__file__':str(here/'check-rc-rebind-owner.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<RC fixture setup>','exec'),ns)
prefix='static unsigned long long receipt_epoch=2,receipt_token=3;\n'+ns['prefix']
prefix=prefix.replace('a->identity.adapter_epoch==2','a->identity.adapter_epoch==receipt_epoch').replace('{2,2,3,observed_serial','{receipt_epoch,2,receipt_token,observed_serial')
prefix=prefix.replace('a->request_id[0]==3','(a->request_id[0]==3||a->request_id[0]==5)').replace('r->open_request_id[0]==3','(r->open_request_id[0]==3||r->open_request_id[0]==5)').replace('r->open_token==3','r->open_token==receipt_token')
body=ns['body'].replace('static unsigned probes,submits;', 'static unsigned probes,submits,next_epoch=2,next_id=3,probe_fail_after;static int mode_router=1,probe_ok=1;')
body=body.replace('(struct wr_iot_rc_mode){1,1,0}','(struct wr_iot_rc_mode){mode_router,1,0}')
a=body.index('int wr_iot_rebind_configuration_current(');b=body.index('\nint wr_iot_rebind_network_step',a)
body=body[:a]+r'''int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*p,const unsigned char*n,struct wr_iot_driver_identity*out){
 assert(depth&&p->epoch+1==next_epoch&&p->action==WR_STOP_RELEASE&&n[0]==next_id);probes++;
 if(!probe_ok)return 0;
 if(probe_fail_after&&!--probe_fail_after){guard_invalid=1;return 0;}
 *out=(struct wr_iot_driver_identity){next_epoch,2};return 1;
}'''+body[b:]
a=body.index('int wr_iot_rebind_open_submit(');b=body.index('\nint wr_iot_rebind_open_recovery',a)
body=body[:a]+r'''int wr_iot_rebind_open_submit(struct wr_iot_rebind_open_controller*s,const struct wr_iot_physical_rebind_request*r){
 assert(r->physical.epoch+1==next_epoch&&r->open.adapter_epoch==next_epoch&&r->open.request_id[0]==next_id);
 s->owner=getpid();s->phase=WR_REBIND_OPEN_RETAINED;s->attempt.identity=(struct wr_iot_driver_identity){next_epoch,2};memcpy(s->attempt.request_id,r->open.request_id,16);
 live_epoch=receipt_epoch=next_epoch;live_token=receipt_token=next_id;submits++;return 1;
}
int wr_iot_rebind_open_current(struct wr_iot_rebind_open_controller*s,struct wr_iot_driver_open_current_result*r){s->phase=WR_REBIND_OPEN_CURRENT;*r=(struct wr_iot_driver_open_current_result){live_epoch,2,live_token};return 1;}
'''+body[b:]
body=body.replace('a->request_id[0]==3','(a->request_id[0]==3||a->request_id[0]==5)').replace('(struct wr_iot_driver_open_recovery_result){2,2,3}', '(struct wr_iot_driver_open_recovery_result){receipt_epoch,2,receipt_token}')
a=body.index(' assert(submits==1&&closes==1&&progresses==1&&releases==1);')
body=body[:a]+r'''
 struct wr_iot_control_request again={.id="05050505050505050505050505050505",.created=5,.request=desired};
 struct wr_iot_physical_stop_request next={.action=WR_STOP_RELEASE,.epoch=2,.generation=2,.open_token=3,.closed_serial=observed_serial,.attempt=8,.nonce={2}};
 struct wr_iot_rebind_owner completed=rebind;
 next.closed_serial++;assert(!wr_iot_rc_rebind_begin(&again,&next)&&!memcmp(&completed,&rebind,sizeof(rebind)));next.closed_serial--;
 mode_router=0;assert(!wr_iot_rc_rebind_begin(&again,&next)&&!memcmp(&completed,&rebind,sizeof(rebind)));mode_router=1;
 next_epoch=3;next_id=5;probe_ok=0;
 assert(!wr_iot_rc_rebind_begin(&again,&next)&&!memcmp(&completed,&rebind,sizeof(rebind))&&rebind.stop.active==&rebind.start&&!depth);probe_ok=1;
 assert(wr_iot_rc_rebind_begin(&again,&next)&&rebind.phase==WR_REBIND_OWNER_START&&rebind.start.start.identity.adapter_epoch==3&&depth==1);
 assert(!wr_iot_rc_rebind_begin(&again,&next));
 for(unsigned i=0;i<12&&rebind.phase!=WR_REBIND_OWNER_ACTIVE;i++)(void)wr_iot_activation_continue(again.id,again.created);
 assert(rebind.phase==WR_REBIND_OWNER_ACTIVE&&submits==2&&!depth);
 strcpy(result.id,again.id);result.created=again.created;assert(wr_iot_rc_backend_observed(&result));
 struct wr_iot_control_request off_again={.id="06060606060606060606060606060606",.created=6};
 observed_serial++;
 assert(wr_iot_activation_execute(&off_again)==WR_IOT_RESULT_RECOVERY&&rebind.phase==WR_REBIND_OWNER_STOP);
 for(unsigned i=0;i<60&&rebind.phase!=WR_REBIND_OWNER_OFF;i++)(void)wr_iot_activation_continue(off_again.id,off_again.created);
 assert(rebind.phase==WR_REBIND_OWNER_OFF&&!depth&&closes==2&&progresses==2&&releases==2);
 assert(wr_iot_rc_backend_closed(&receipt)&&receipt.adapter_epoch==3&&receipt.open_token==5&&receipt.close_serial==observed_serial);
 /* A third admission with failed read-only snapshot cancellation must retain
  * the new owner/guard, never restore the previous completed OFF over it. */
 next=(struct wr_iot_physical_stop_request){.action=WR_STOP_RELEASE,.epoch=3,.generation=2,.open_token=5,.closed_serial=observed_serial,.attempt=9,.nonce={3}};
 again.created=7;strcpy(again.id,"07070707070707070707070707070707");
 next_epoch=4;next_id=7;probe_fail_after=2;
 assert(!wr_iot_rc_rebind_begin(&again,&next)&&rebind.phase==WR_REBIND_OWNER_START&&rebind.start.phase==WR_IOT_RUN_UNCERTAIN);
 assert(rebind.start.start.admission.snapshot.active&&rebind.start.start.admission.snapshot.token==1&&depth==1&&rebind.start.input.id[1]=='7');
 guard_invalid=0;
 assert(wr_iot_activation_continue(again.id,again.created)==WR_IOT_RESULT_RECOVERY&&depth==1&&submits==2);
 puts("PASS repeated RC rebind admission: epoch2 OFF -> epoch3 ACTIVE/OFF with actual snapshots/commit/OFF, stale tuple and invalid mode/read-only refusal preserve exact completed context/internal pointer; epoch4 partial snapshot retains new owner/guard instead of restoring; physical completion/network/driver adapters injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rc-rebind-repeat-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';binary=Path(d)/'check'
 units=('rebind-owner.c','rebind-runner.c','rebind-start.c','rebind-rollback.c','rebind-close.c','rebind-closed-rollback.c','rebind-commit.c','rebind-active-stop.c','rebind-observe.c','precreated-stop.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c','activation-observe.c','activation-owner.c','active-stop.c','start-runner.c','start-admission.c','initial-off.c','start-network-rollback.c','start-close.c','start-closed-rollback.c')
 unit.write_text(prefix+'\n#include "check-reopen-unused.h"\n'+body.replace('#include "rc-backend.c"','#include "check-legacy-start-unused.h"\n#include "rc-backend.c"'))
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
