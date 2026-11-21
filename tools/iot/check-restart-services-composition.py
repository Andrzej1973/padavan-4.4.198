"""Actual service controller and extracted actual SDK adapters; commands injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-service-policy.py').read_text())
node=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
prefix=next(n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and isinstance(n.value,str) and '#include <assert.h>' in n.value)
tree=ast.parse((here/'prepare-rc.py').read_text())
helper=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets))
a=helper.index('int wr_iot_rc_restart_service_policy(');b=helper.index('/* Profile generation only;',a)
code=prefix+helper[a:b]+r'''
#include "restart-services.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int main_ok=1;
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main*m){assert(m);return main_ok;}
#include "restart-services.c"
int main(void){
 struct wr_iot_restart_main main={0};wr_iot_rc_shutdown.active=1;enterprise=1;
 for(int fault=0;fault<3;fault++){
  struct wr_iot_restart_services s={0};calls=reads=fail=0;
  assert(wr_iot_restart_services_begin(&s,&main));
  guard=0;assert(!wr_iot_restart_services_step(&s)&&!calls&&!s.attempted);guard=1;
  for(int slot=0;slot<3;slot++){
   fail=slot==fault;assert(!wr_iot_restart_services_step(&s));
   if(fail){
    assert(s.phase==WR_SERVICES_UNCERTAIN&&calls==slot+1);
    fail=0;for(int i=0;i<3;i++)assert(!wr_iot_restart_services_step(&s)&&calls==slot+1);
    break;
   }
  }
 }
 struct wr_iot_restart_services s={0};calls=reads=fail=0;
 assert(wr_iot_restart_services_begin(&s,&main));
 for(int i=0;i<3;i++)assert(!wr_iot_restart_services_step(&s));
 assert(wr_iot_restart_services_step(&s)&&calls==3);
 running=0;assert(!wr_iot_rc_restart_auth_process_current(&s.policy));running=1;
 assert(wr_iot_rc_restart_auth_process_current(&s.policy));
 kick=-70;assert(!wr_iot_restart_services_step(&s)&&calls==3);kick=-75;
 assert(wr_iot_restart_services_step(&s)&&calls==3);
 puts("PASS actual service controller/SDK composition: guarded ordered daemon/RSSI calls, each command failure retained without replay, policy drift refusal, daemon-name observation independent of submitted commands; kernel/process/command actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-services-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
