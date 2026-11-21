#!/usr/bin/env python3
"""Actual runner -> CLOSE controller -> closed network rollback composition."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
module=ast.parse((here/'check-rebind-closed-rollback.py').read_text())
body=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
prefix=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
body=body.split('int main(void)',1)[0]+r'''
#include "rebind-runner.h"
int wr_iot_rebind_start_begin(struct wr_iot_rebind_start*s,const struct wr_iot_physical_stop_request*p,const unsigned char*n){(void)s;(void)p;(void)n;assert(0);return 0;}
int wr_iot_rebind_start_stage(struct wr_iot_rebind_start*s,const char*(*r)(void*,const char*),void*c,int a,int b,int d){(void)s;(void)r;(void)c;(void)a;(void)b;(void)d;assert(0);return 0;}
int wr_iot_start_admission_cancel(struct wr_iot_start_admission*s){(void)s;assert(0);return 0;}
int wr_iot_rebind_network_step(struct wr_iot_start_network*n,struct wr_iot_rebind_start*s,const struct wr_iot_request*r){(void)n;(void)s;(void)r;assert(0);return 0;}
int wr_iot_rebind_open_submit(struct wr_iot_rebind_open_controller*s,const struct wr_iot_physical_rebind_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rebind_open_current(struct wr_iot_rebind_open_controller*s,struct wr_iot_driver_open_current_result*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*p,const unsigned char*n,struct wr_iot_driver_identity*r){(void)p;(void)n;(void)r;assert(0);return 0;}
int wr_iot_request_stage_matches(const struct wr_iot_request*r){(void)r;assert(0);return 0;}
int wr_iot_network_check(const char*a,const char*b,const char*c,const char*d){(void)a;(void)b;(void)c;(void)d;assert(0);return 0;}
int wr_iot_bridge_address_matches(const char*a,const char*b){(void)a;(void)b;assert(0);return 0;}
int wr_iot_network_services_ready(const char*a){(void)a;assert(0);return 0;}
int wr_iot_active_filter_ready_current(void){assert(0);return 0;}
int wr_iot_active_filter_observed_current(void){assert(0);return 0;}
int wr_iot_rebind_commit_step(struct wr_iot_start_commit*c,struct wr_iot_rebind_start*s,const struct wr_iot_start_network*n,const struct wr_iot_rebind_open_controller*o,const struct wr_iot_request*r){(void)c;(void)s;(void)n;(void)o;(void)r;assert(0);return 0;}
int wr_iot_rebind_rollback_step(struct wr_iot_start_network_rollback*r,struct wr_iot_start_network*n,struct wr_iot_rebind_start*s,const struct wr_iot_rebind_open_controller*o){(void)r;(void)n;(void)s;(void)o;assert(0);return 0;}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop*s,const struct wr_iot_driver_attempt*a){(void)s;(void)a;assert(0);return 0;}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop*s){(void)s;assert(0);return 0;}
#include "rebind-runner.c"
int main(void){
 struct wr_iot_rebind_runner s={.owner=getpid(),.phase=WR_IOT_RUN_CLOSE,
  .start={.owner=getpid(),.identity={2,2},.open_id={1},
   .physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}},
   .admission={.admitted=1,.mutation_started=1,.staged=1,.reopened=2}},
  .open={.attempt={{2,2},{1}},.owner=getpid(),.phase=WR_REBIND_OPEN_RETAINED},
  .network={.phase=WR_IOT_NET_RECOVERY,.attempted=127}};
 s.start.admission.snapshot.active=s.start.admission.snapshot.token=1;
 s.start.admission.snapshot.owner=getpid();wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
 close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY&&closes==1);
 progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
 for(unsigned i=0;i<3;i++)assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY&&closes==1&&bridge);
 progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 for(unsigned i=0;i<3;i++)assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
 assert(s.phase==WR_IOT_RUN_CLOSED_ROLLBACK&&s.start.admission.snapshot.active&&closes==1);
 resource_fail=1;assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY&&s.rollback.phase==WR_IOT_ROLL_BRIDGE_DOWN&&bridge);
 resource_fail=0;observed_serial++;
 assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY&&bridge&&!finished);observed_serial--;
 enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
 for(unsigned i=0;i<8&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_rebind_runner_step(&s);
 assert(result==WR_IOT_RESULT_REJECTED&&finished==1&&!bridge&&!s.start.admission.snapshot.active&&closes==1);
 assert(wr_iot_rc_shutdown.pending==SIGTERM&&wr_iot_rc_shutdown.active);
 assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_REJECTED&&finished==1&&closes==1);
 puts("PASS actual rebind runner/CLOSE controller/post-CLOSE rollback composition: uncertain CLOSE once, pending retains bridge, fresh serial before cleanup, resource failure retains phase, snapshot finish once, pending shutdown retained; driver/resources injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-rebind-runner-close-') as d:
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
