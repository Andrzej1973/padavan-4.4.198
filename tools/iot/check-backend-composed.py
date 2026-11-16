from pathlib import Path
import ast,subprocess,tempfile,sys
here=Path(__file__).resolve().parent;root=Path(__file__).resolve().parent
source=(here/'check-rc-backend-composition.py').read_text();ns={'__file__':str(here/'check-rc-backend-composition.py')};exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<actual backend fixture>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
body=ns['body'].split('int main(void)',1)[0].replace('#include "rc-backend.c"','#define WR_IOT_TEST_INITIAL_BACKEND 1\n#include "rc-backend.c"')+r'''
#include "restart-initial-handoff.h"
static int parent_ok=1;
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation*g){(void)g;assert(0);return 0;}
int wr_iot_restart_initial_parent_current(struct wr_iot_restart_restore*s,int before){assert(s->busy==1&&(before==0||before==1));return parent_ok;}
#include "rc-initial-restart-start.inc"
#include "cold-on-owner.h"
int wr_iot_cold_owner_step(struct wr_iot_cold_owner *s){(void)s;assert(0);return 0;}
#include "rc-cold-start.inc"
int main(void){
 assert(candidate_read(NULL,"wr_iot_enable"));reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 wr_iot_rc_shutdown.active=1;
 struct wr_iot_control_request input={.id="01010101010101010101010101010101",.created=7,
 .request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 struct wr_iot_restart_restore parent={.owner=0,.busy=1,.phase=WR_RESTORE_HANDOFF,.handoff_created=7};
 parent.owner=getpid();memset(parent.open_id,1,16);parent.main.identity=(struct wr_iot_driver_identity){1,2};parent.generation.origin.desired=input.request;
 parent_ok=0;assert(!wr_iot_rc_initial_restart_start_begin(&parent,&input)&&!backend.start.owner&&!depth);parent_ok=1;
 assert(wr_iot_rc_initial_restart_start_begin(&parent,&input)&&backend.start.owner==getpid());parent.initial_start_claimed=1;
 assert(!wr_iot_rc_initial_restart_start_begin(&parent,&input));
 for(unsigned i=0;i<30&&backend.phase==WR_IOT_OWNER_START;i++)assert(wr_iot_rc_initial_restart_start_progress(&parent,&input));
 assert(backend.phase==WR_IOT_OWNER_ACTIVE&&backend.start.phase==WR_IOT_RUN_ACTIVE);
 assert(wr_iot_rc_initial_restart_active_current(&parent,&input));
 filter_ok=0;assert(!wr_iot_rc_initial_restart_active_current(&parent,&input));filter_ok=1;
 services_ok=0;assert(!wr_iot_rc_initial_restart_active_current(&parent,&input));services_ok=1;
 live_token++;assert(!wr_iot_rc_initial_restart_active_current(&parent,&input));live_token--;
 parent_ok=0;assert(!wr_iot_rc_initial_restart_active_current(&parent,&input));parent_ok=1;
 assert(wr_iot_rc_initial_restart_active_current(&parent,&input));
 struct wr_iot_activation_owner backend_before=backend;struct wr_iot_control_result result={.state=WR_IOT_RESULT_APPLIED,.created=7};strcpy(result.id,input.id);
 assert(!wr_iot_rc_boot_idle());
 assert(wr_iot_activation_execute(&input)==WR_IOT_RESULT_RECOVERY);
 assert(wr_iot_activation_continue(input.id,input.created)==WR_IOT_RESULT_RECOVERY);
 assert(!wr_iot_rc_backend_observed(&result)&&!wr_iot_activation_prepare_radio_stop());
 struct wr_iot_rc_quiesce q={0};struct wr_iot_control_request off={.id="02020202020202020202020202020202",.created=9};
 assert(!wr_iot_rc_quiesce_begin(&q,&off)&&!q.owner);
 struct wr_iot_physical_stop_request stop={0};assert(!wr_iot_rc_rebind_begin(&input,&stop));
 struct wr_iot_cold_owner cold={0};
 assert(!wr_iot_rc_cold_start_begin(&cold,&input));
 assert(!wr_iot_rc_cold_start_progress(&cold,&input));
 assert(!wr_iot_rc_cold_active_current(&cold,&input));
 assert(!memcmp(&backend,&backend_before,sizeof(backend)));
 assert(wr_iot_rc_initial_restart_active_current(&parent,&input));
 return 0; /* Retained live owner exits fixture, not production terminal cleanup. */
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-backend-composed-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d);(p/'check.c').write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 units_dir=p/'units';units_dir.mkdir();compile_units=[]
 for n in units:
  source=(root if n in ('start-runner.c','start-closed-rollback.c') else here)/n
  unit=units_dir/n;unit.write_bytes(source.read_bytes());compile_units.append(str(unit))
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(root),str(p/'check.c'),*compile_units,'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=20)
print('PASS candidate INITIAL backend + actual activation-owner/START runner/admission/snapshot/staging/full ACTIVE observer; resource/driver and prepared-parent actors, no device OPEN claim')
