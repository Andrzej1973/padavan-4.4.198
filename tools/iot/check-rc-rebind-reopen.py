#!/usr/bin/env python3
"""Actual rebind OFF -> same-epoch legacy CLOSED-reopen -> normal OFF."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-rebind-owner.py').read_text();ns={'__file__':str(here/'check-rc-rebind-owner.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<RC rebind fixture setup>','exec'),ns)
prefix='static unsigned long long handoff_closed_token=3;\n'+ns['prefix']
prefix=prefix.replace('a->request_id[0]==3','(a->request_id[0]==3||a->request_id[0]==5)').replace('r->open_request_id[0]==3','(r->open_request_id[0]==3||r->open_request_id[0]==5)')
prefix=prefix.replace('r->open_token==3','r->open_token==(r->open_request_id[0]==3?3:5)')
prefix=prefix.replace('{2,2,3,observed_serial','{2,2,handoff_closed_token,observed_serial')
prefix=prefix.replace('closes++;return close_result;', 'if(r->open_request_id[0]==5)observed_serial++;closes++;return close_result;')
body=ns['body'].replace('a->request_id[0]==3','(a->request_id[0]==3||a->request_id[0]==5)').replace('(struct wr_iot_driver_open_recovery_result){2,2,3}', '(struct wr_iot_driver_open_recovery_result){2,2,live_token}')
body=body.replace('static unsigned probes,submits;', 'static unsigned probes,submits,standard_submits;static int mode_router=1;')
body=body.replace('(struct wr_iot_rc_mode){1,1,0}', '(struct wr_iot_rc_mode){mode_router,1,0}')
hooks=r'''
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const unsigned char*i){(void)n;(void)a;(void)r;(void)i;assert(0);return 0;}
int wr_iot_reopen_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const struct wr_iot_reopen_witness*w){
 assert(a->reopened==1&&r->enabled&&w->attempt.identity.adapter_epoch==2&&w->attempt.request_id[0]==3&&wr_iot_reopen_witness_current(w));
 n->phase=WR_IOT_NET_READY;n->attempted=127;bridge_index=7;rollback_dns=1;strcpy(values[8].value,"1");strcpy(values[9].value,"1");return 1;
}
enum wr_iot_driver_submit_result wr_iot_driver_open_requested_tracked(const char*id,const struct wr_iot_request*r,struct wr_iot_driver_attempt*a){
 assert(id[0]=='0'&&id[1]=='5'&&r->enabled);a->identity=(struct wr_iot_driver_identity){2,2};memset(a->request_id,5,16);
 live_token=handoff_closed_token=5;standard_submits++;return WR_IOT_DRIVER_OPEN_COMPLETED;
}
'''
body=body.replace('int main(void){',hooks+'int main(void){')
a=body.index(' assert(submits==1&&closes==1&&progresses==1&&releases==1);')
body=body[:a]+r'''
 struct wr_iot_control_request again={.id="05050505050505050505050505050505",.created=5,.request=desired};
 unsigned physical_probes=probes;
 mode_router=0;assert(wr_iot_activation_execute(&again)==WR_IOT_RESULT_REJECTED&&rebind.owner&&backend.phase==WR_IOT_OWNER_IDLE&&!depth);mode_router=1;
 struct wr_iot_rc_quiesce retained_off={0};assert(wr_iot_rc_quiesce_begin(&retained_off,&off)&&retained_off.complete&&!retained_off.resume_needed);
 observed_serial++;assert(wr_iot_activation_execute(&again)==WR_IOT_RESULT_RECOVERY&&rebind.owner&&!backend.start.owner&&!depth);observed_serial--;
 assert(wr_iot_activation_execute(&again)==WR_IOT_RESULT_RECOVERY&&!rebind.owner&&backend.phase==WR_IOT_OWNER_START&&depth==1);
 assert(backend.start.prior_closed.valid&&backend.start.prior_closed.attempt.identity.adapter_epoch==2&&backend.start.prior_closed.attempt.request_id[0]==3);
 assert(!idle_reads); /* No initial never-opened fallback. */
 for(unsigned i=0;i<15&&backend.phase!=WR_IOT_OWNER_ACTIVE;i++)(void)wr_iot_activation_continue(again.id,again.created);
 assert(backend.phase==WR_IOT_OWNER_ACTIVE&&standard_submits==1&&submits==1&&probes==physical_probes&&!depth&&!idle_reads);
 strcpy(result.id,again.id);result.created=again.created;assert(wr_iot_rc_backend_observed(&result));
 struct wr_iot_control_request off_again={.id="06060606060606060606060606060606",.created=6};
 assert(wr_iot_activation_execute(&off_again)==WR_IOT_RESULT_RECOVERY&&backend.phase==WR_IOT_OWNER_STOP);
 for(unsigned i=0;i<60&&backend.phase!=WR_IOT_OWNER_OFF;i++)(void)wr_iot_activation_continue(off_again.id,off_again.created);
 assert(backend.phase==WR_IOT_OWNER_OFF&&!depth&&closes==2&&progresses==2&&releases==2);
 strcpy(result.id,off_again.id);result.created=off_again.created;
 assert(wr_iot_rc_backend_observed(&result)&&wr_iot_rc_backend_closed(&receipt)&&receipt.adapter_epoch==2&&receipt.open_token==5&&receipt.close_serial==observed_serial);
 assert(!backend.start.input.request.password[0]&&!idle_reads&&probes==physical_probes);
 puts("PASS actual RC rebind OFF -> CLOSED-reopen -> normal OFF: fresh tuple/witness, invalid mode and serial drift preserve source owner, no live context copy/initial-idle/physical rebind replay, new stable legacy runner ACTIVE, subsequent public OFF and new token/serial; network and driver adapters injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rc-rebind-reopen-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('rebind-owner.c','rebind-runner.c','rebind-start.c','rebind-rollback.c','rebind-close.c','rebind-closed-rollback.c','rebind-commit.c','rebind-active-stop.c','rebind-observe.c','precreated-stop.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c','activation-observe.c','activation-owner.c','active-stop.c','start-runner.c','start-admission.c','initial-off.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','reopen-start.c','reopen-admission.c','reopen-rollback.c','driver-open-controller.c','start-commit.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
