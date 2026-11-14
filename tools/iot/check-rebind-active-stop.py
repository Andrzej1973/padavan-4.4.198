#!/usr/bin/env python3
"""Actual rebind normal OFF/snapshots/CLOSE and read-only observations."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
prefix=prefix.replace('a->identity.adapter_epoch==1','a->identity.adapter_epoch==2').replace('{1,2,3,observed_serial}','{2,2,3,observed_serial}')
prefix='static int closed_drift_after;\n'+prefix
prefix=prefix.replace('3,observed_serial};return 1;}', '3,observed_serial+(closed_drift_after>0&&!--closed_drift_after)};return 1;}')
prefix+=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
body=r'''
#include "rebind-observe.h"
static int services_ok=1,filter_ok=1;
static unsigned long long live_token=3,live_epoch=2,live_generation=2;
int wr_iot_network_services_ready(const char*g){assert(depth&&g);return services_ok;}
int wr_iot_active_filter_observed_current(void){assert(depth);return filter_ok;}
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt*a,struct wr_iot_driver_open_current_result*r){assert(depth&&a);*r=(struct wr_iot_driver_open_current_result){live_epoch,live_generation,live_token};return 1;}
int wr_iot_driver_open_recovery_read(const struct wr_iot_driver_attempt*a,struct wr_iot_driver_open_recovery_result*r){assert(a->request_id[0]==1);*r=(struct wr_iot_driver_open_recovery_result){2,2,3};return 1;}
int main(void){
 reset();rollback_dns=0;abort_calls=0;closes=progresses=releases=0;
 close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 wr_iot_rc_shutdown.active=1;
 struct wr_iot_rebind_runner s={.owner=getpid(),.phase=WR_IOT_RUN_ACTIVE,
  .input={.id="01010101010101010101010101010101",.created=1},
  .start={.owner=getpid(),.identity={2,2},.open_id={1},.admission={.admitted=1,.mutation_started=1,.staged=1,.reopened=2}},
  .open={.owner=getpid(),.phase=WR_REBIND_OPEN_CURRENT,.attempt={{2,2},{1}}},
  .commit={.owner=getpid(),.phase=WR_IOT_COMMIT_ACTIVE,.open_token=3,.attempt={{2,2},{1}}},
  .network={.phase=WR_IOT_NET_READY,.attempted=127}};
 /* Construct owned ACTIVE settings through real snapshot/stage/suspend,
  * without copying a live runner or claiming the startup path was executed. */
 assert(wr_iot_request_read(&s.input.request,candidate_read,NULL,1,1,0,NULL,0));
 assert(wr_iot_request_snapshot_take(&s.start.admission.snapshot));
 assert(wr_iot_request_stage_from(candidate_read,NULL,1,1,0));
 bridge_index=7;strcpy(values[8].value,"1");strcpy(values[9].value,"1");
 assert(wr_iot_request_snapshot_suspend(&s.start.admission.snapshot)&&!depth);
 struct wr_iot_control_result observed={.id="01010101010101010101010101010101",.created=1,.state=WR_IOT_RESULT_APPLIED};
 assert(wr_iot_rebind_active_observed(&s,&observed)&&!depth);
 struct wr_iot_rebind_runner before=s;int before_writes=writes;
 for(unsigned field=7;field<16;field++){
  char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign");
  assert(!wr_iot_rebind_active_observed(&s,&observed)&&!depth);strcpy(values[field].value,saved);
 }
 services_ok=0;assert(!wr_iot_rebind_active_observed(&s,&observed));services_ok=1;
 filter_ok=0;assert(!wr_iot_rebind_active_observed(&s,&observed));filter_ok=1;
 live_epoch=3;assert(!wr_iot_rebind_active_observed(&s,&observed));live_epoch=2;
 live_generation=3;assert(!wr_iot_rebind_active_observed(&s,&observed));live_generation=2;
 live_token=4;assert(!wr_iot_rebind_active_observed(&s,&observed));live_token=3;
 s.commit.attempt.request_id[1]=1;assert(!wr_iot_rebind_active_observed(&s,&observed));s.commit.attempt.request_id[1]=0;
 s.open.busy=1;assert(!wr_iot_rebind_active_observed(&s,&observed));s.open.busy=0;
 rollback_dns=1;assert(!wr_iot_rebind_active_observed(&s,&observed));rollback_dns=0;
 assert(!memcmp(&before,&s,sizeof(s))&&writes==before_writes&&!depth);
 struct wr_iot_control_request off={.id="02020202020202020202020202020202",.created=2};
 struct wr_iot_rebind_active_stop stop={0};
 strcpy(values[11].value,"foreign password");assert(!wr_iot_rebind_active_stop_begin(&stop,&s,&off)&&!depth);strcpy(values[11].value,"password123");
 assert(wr_iot_rebind_active_stop_begin(&stop,&s,&off)&&stop.active==&s&&depth==1);
 assert(!wr_iot_rebind_active_stop_begin(&stop,&s,&off));
 assert(!wr_iot_rebind_active_observed(&s,&observed));
 assert(wr_iot_rebind_active_stop_continue(&stop,s.input.id,2)==WR_IOT_RESULT_RECOVERY&&!closes);
 assert(wr_iot_rebind_active_stop_continue(&stop,off.id,3)==WR_IOT_RESULT_RECOVERY&&!closes);
 while(stop.stop.phase!=WR_IOT_STOP_ISOLATE)
  assert(wr_iot_rebind_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
 assert(depth==3&&s.start.admission.snapshot.active&&closes==1);
 quarantine_ready=0;
 for(unsigned i=0;i<3;i++)assert(wr_iot_rebind_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_RECOVERY&&depth==3&&closes==1);
 quarantine_ready=1;
 enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
 for(unsigned i=0;i<55&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_rebind_active_stop_continue(&stop,off.id,off.created);
 assert(result==WR_IOT_RESULT_APPLIED&&!depth&&!s.start.admission.snapshot.active&&s.phase==WR_IOT_RUN_STOPPED&&closes==1&&progresses==1&&releases==1&&!abort_calls);
 struct wr_iot_request empty={0};assert(!memcmp(&s.input.request,&empty,sizeof(empty)));
 for(unsigned i=0;i<9;i++)assert(!strcmp(i<3?"0":"",values[7+i].value));
 assert(!wr_iot_rebind_off_observed(&s,&stop,&observed));strcpy(observed.id,off.id);observed.created=off.created;
 assert(wr_iot_rebind_off_observed(&s,&stop,&observed)&&!depth);
 struct wr_iot_driver_closed_result receipt={0};
 assert(wr_iot_rebind_off_closed(&s,&stop,&observed,&receipt)&&receipt.adapter_epoch==2&&receipt.close_serial==observed_serial&&!depth);
 closed_drift_after=2;assert(!wr_iot_rebind_off_closed(&s,&stop,&observed,&receipt)&&!receipt.close_serial&&!depth&&!closed_drift_after);
 observed_serial++;assert(!wr_iot_rebind_off_closed(&s,&stop,&observed,&receipt)&&!receipt.close_serial&&!depth);observed_serial--;
 for(unsigned field=7;field<16;field++){
  char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign OFF");
  assert(!wr_iot_rebind_off_observed(&s,&stop,&observed)&&!depth);strcpy(values[field].value,saved);
 }
 assert(wr_iot_rebind_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_APPLIED&&closes==1);
 puts("PASS retained rebind ACTIVE/OFF observation and actual normal OFF: snapshot/stage/suspend/resume, nine foreign fields, epoch/generation/token/nonce refusal, CLOSE once, three guards retained across isolation failure, baseline discarded and credentials cleared, fresh released CLOSE; driver/resources injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-rebind-active-stop-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('rebind-active-stop.c','rebind-observe.c','precreated-stop.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
