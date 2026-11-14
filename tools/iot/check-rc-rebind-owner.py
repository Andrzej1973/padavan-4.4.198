#!/usr/bin/env python3
"""Actual RC routing, rebind owner/runner/admission/commit/OFF/observers."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rebind-active-stop.py').read_text();ns={'__file__':str(here/'check-rebind-active-stop.py')}
exec(compile(source[:source.index('with tempfile.TemporaryDirectory(')],'<rebind fixture setup>','exec'),ns)
body=ns['body'].split('int main(void){',1)[0]+r'''
#include "rc-backend.c"
static unsigned probes,submits;
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*m){assert(depth);*m=(struct wr_iot_rc_mode){1,1,0};return 1;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*p,const unsigned char*n,struct wr_iot_driver_identity*out){assert(depth&&p->epoch==1&&p->action==WR_STOP_RELEASE&&n[0]==3);probes++;*out=(struct wr_iot_driver_identity){2,2};return 1;}
int wr_iot_rebind_network_step(struct wr_iot_start_network*n,struct wr_iot_rebind_start*s,const struct wr_iot_request*r){assert(s->admission.staged&&r->enabled);n->phase=WR_IOT_NET_READY;n->attempted=127;bridge_index=7;rollback_dns=1;strcpy(values[8].value,"1");strcpy(values[9].value,"1");return 1;}
int wr_iot_rebind_open_submit(struct wr_iot_rebind_open_controller*s,const struct wr_iot_physical_rebind_request*r){assert(r->physical.epoch==1&&r->open.adapter_epoch==2&&r->open.request_id[0]==3);s->owner=getpid();s->phase=WR_REBIND_OPEN_RETAINED;s->attempt.identity=(struct wr_iot_driver_identity){2,2};memcpy(s->attempt.request_id,r->open.request_id,16);submits++;return 1;}
int wr_iot_rebind_open_current(struct wr_iot_rebind_open_controller*s,struct wr_iot_driver_open_current_result*r){s->phase=WR_REBIND_OPEN_CURRENT;*r=(struct wr_iot_driver_open_current_result){2,2,3};return 1;}
int wr_iot_rebind_open_recovery(const struct wr_iot_rebind_open_controller*s,struct wr_iot_driver_open_recovery_result*r){return wr_iot_driver_open_recovery_read(&s->attempt,r);}
int wr_iot_active_filter_ready_current(void){assert(depth);return 1;}
int wr_iot_dns_activation_commit(void){assert(depth&&rollback_dns==1);rollback_dns=0;return 1;}
int main(void){
 reset();rollback_dns=0;wr_iot_rc_shutdown.active=1;close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 /* Old OFF is an injected completed provenance context. Actual new admission,
  * staging, snapshots, commit, OFF and routing are executed below. */
 backend.owner=getpid();backend.phase=WR_IOT_OWNER_OFF;
 backend.start.owner=backend.stop.owner=getpid();
 backend.start.phase=WR_IOT_RUN_STOPPED;backend.start.open.attempt.identity=(struct wr_iot_driver_identity){1,2};
 strcpy(backend.start.input.id,"01010101010101010101010101010101");backend.start.input.created=1;
 backend.stop.active=&backend.start;backend.stop.complete=1;backend.stop.stop.phase=WR_IOT_STOP_COMPLETE;
 strcpy(backend.stop.id,"02020202020202020202020202020202");backend.stop.created=2;
 backend.stop.stop.close.phase=WR_IOT_CLOSE_OWNER_RELEASED;backend.stop.stop.close.request.open_token=3;
 backend.stop.stop.close_serial=observed_serial;
 struct wr_iot_control_request on={.id="03030303030303030303030303030303",.created=3};
 assert(wr_iot_request_read(&on.request,candidate_read,NULL,1,1,0,NULL,0));
 struct wr_iot_physical_stop_request physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=observed_serial,.attempt=7,.nonce={1}};
 physical.closed_serial++;assert(!wr_iot_rc_rebind_begin(&on,&physical)&&!rebind.owner&&!probes);physical.closed_serial--;
 physical.epoch++;assert(!wr_iot_rc_rebind_begin(&on,&physical)&&!rebind.owner&&!probes);physical.epoch--;
 assert(wr_iot_rc_rebind_begin(&on,&physical)&&rebind.owner==getpid()&&rebind.phase==WR_REBIND_OWNER_START&&depth==1);
 assert(!wr_iot_rc_rebind_begin(&on,&physical));
 assert(wr_iot_activation_continue(on.id,4)==WR_IOT_RESULT_RECOVERY&&depth==1);
 for(unsigned i=0;i<10&&rebind.phase!=WR_REBIND_OWNER_ACTIVE;i++)(void)wr_iot_activation_continue(on.id,on.created);
 assert(rebind.phase==WR_REBIND_OWNER_ACTIVE&&submits==1&&!depth);
 struct wr_iot_control_result result={.id="03030303030303030303030303030303",.created=3,.state=WR_IOT_RESULT_APPLIED};
 assert(wr_iot_rc_backend_observed(&result));
 strcpy(result.id,backend.start.input.id);result.created=backend.start.input.created;
 assert(!wr_iot_rc_backend_observed(&result));strcpy(result.id,on.id);result.created=on.created;
 live_token=4;assert(!wr_iot_rc_backend_observed(&result));live_token=3;
 assert(!wr_iot_activation_prepare_radio_stop());
 struct wr_iot_driver_closed_result receipt={0};assert(!wr_iot_rc_backend_closed(&receipt)&&!receipt.close_serial);
 struct wr_iot_control_request off={.id="04040404040404040404040404040404",.created=4};
 struct wr_iot_driver_identity expected_identity={2,2};
 assert(wr_iot_rc_rebind_active_current(&on,&physical,&expected_identity));
 expected_identity.adapter_epoch++;assert(!wr_iot_rc_rebind_active_current(&on,&physical,&expected_identity));expected_identity.adapter_epoch--;
 physical.attempt++;assert(!wr_iot_rc_rebind_active_current(&on,&physical,&expected_identity));physical.attempt--;
 on.created++;assert(!wr_iot_rc_rebind_active_current(&on,&physical,&expected_identity));on.created--;
 on.request.password[0]='X';assert(!wr_iot_rc_rebind_active_current(&on,&physical,&expected_identity));on.request.password[0]=rebind.start.input.request.password[0];
 assert(wr_iot_rc_rebind_active_current(&on,&physical,&expected_identity));
 struct wr_iot_rc_quiesce q={0};struct wr_iot_request desired=rebind.start.input.request;
 assert(wr_iot_rc_quiesce_begin(&q,&off)&&q.resume_needed&&q.active&&rebind.phase==WR_REBIND_OWNER_STOP);
 assert(!memcmp(&q.desired,&desired,sizeof(desired)));
 assert(wr_iot_activation_execute(&off)==WR_IOT_RESULT_RECOVERY); /* No replay during STOP. */
 assert(wr_iot_activation_continue(on.id,on.created)==WR_IOT_RESULT_RECOVERY);
 assert(wr_iot_activation_continue(off.id,off.created)==WR_IOT_RESULT_RECOVERY);
 quarantine_ready=0;
 for(unsigned i=0;i<30&&rebind.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)assert(!wr_iot_rc_quiesce_advance(&q,&receipt));
 assert(rebind.stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3&&closes==1);
 for(unsigned i=0;i<3;i++)assert(!wr_iot_rc_quiesce_advance(&q,&receipt)&&depth==3&&closes==1);
 quarantine_ready=1;
 for(unsigned i=0;i<60&&!q.complete;i++)(void)wr_iot_rc_quiesce_advance(&q,&receipt);
 assert(q.complete&&q.resume_needed&&!q.active&&!depth&&rebind.phase==WR_REBIND_OWNER_OFF&&receipt.adapter_epoch==2);
 assert(!rebind.start.input.request.password[0]&&!memcmp(&q.desired,&desired,sizeof(desired)));
 strcpy(result.id,off.id);result.created=off.created;
 assert(wr_iot_rc_backend_observed(&result)&&wr_iot_rc_backend_closed(&receipt)&&receipt.close_serial==observed_serial);
 struct wr_iot_rc_quiesce already={0};assert(wr_iot_rc_quiesce_begin(&already,&off)&&already.complete&&!already.resume_needed);
 observed_serial++;assert(!wr_iot_rc_backend_closed(&receipt)&&!receipt.close_serial);observed_serial--;
 assert(wr_iot_activation_execute(&on)==WR_IOT_RESULT_REJECTED); /* Stale ON ID must remain refused; fresh re-ON is checked separately. */
 assert(submits==1&&closes==1&&progresses==1&&releases==1);
 puts("PASS actual RC rebind routing/owner/runner/admission/commit/OFF/observer: old tuple mismatch refused, stable owner, CURRENT active status, private quiesce and public continuation routed to same runner, guard retention, desired settings survive OFF, new-epoch CLOSED; network/driver and old OFF provenance injected; stale ON refused; fresh reopen covered separately");
}
'''
# New OPEN nonce is3; existing fixed transport fixture uses1. Validate the new
# identity consistently instead of weakening its assertion.
prefix=ns['prefix'].replace('a->request_id[0]==1','a->request_id[0]==3').replace('r->open_request_id[0]==1','r->open_request_id[0]==3')
body=body.replace('a->request_id[0]==1','a->request_id[0]==3')
with tempfile.TemporaryDirectory(prefix='wr-rc-rebind-owner-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('rebind-owner.c','rebind-runner.c','rebind-start.c','rebind-rollback.c','rebind-close.c','rebind-closed-rollback.c','rebind-commit.c','rebind-active-stop.c','rebind-observe.c','precreated-stop.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 # Unreachable legacy RC paths are resolved by the existing real legacy owner.
 units+=('activation-observe.c','activation-owner.c','active-stop.c','start-runner.c','start-admission.c','initial-off.c','start-network-rollback.c','start-close.c','start-closed-rollback.c')
 # Supply initial/reopen network and OPEN adapters only for legacy linking;
 # every one must remain unreachable in this fixture.
 unit.write_text(prefix+'\n#include "check-reopen-unused.h"\n'+body.replace('#include "rc-backend.c"','#include "check-legacy-start-unused.h"\n#include "rc-backend.c"'))
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
