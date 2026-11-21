from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'check-physical-parent-backend-composed.py').read_text()
inject=r'''
# Use the actual resume pump and actual Guest state controller. Device hooks remain actors.
parent=remove_function(parent,'wr_iot_restart_guest_begin')
parent=remove_function(parent,'wr_iot_restart_guest_step')
parent=parent.replace('static int cancel_guest_up=1;', 'static int cancel_guest_up;')
parent+=r"""
static int actual_guest_down_calls;
enum wr_iot_main_bridge_result wr_iot_restart_guest_bridge_attach(void){return WR_MAIN_BRIDGE_ATTACHED;}
int wr_iot_restart_guest_isolation_prepare(int isolate){return isolate==1&&!cancel_guest_up;}
enum wr_iot_restart_up_result wr_iot_restart_guest_up(void){assert(!cancel_guest_up);cancel_guest_up=1;return WR_RESTART_UP_RETURNED;}
enum wr_iot_restart_up_result wr_iot_restart_guest_down(void){actual_guest_down_calls++;cancel_guest_up=0;return WR_RESTART_UP_RETURNED;}
#include "restart-guest-controller.c"
void parent_fixture_guest_down_once(void){assert(actual_guest_down_calls==1);}
"""
a='void parent_fixture_prepare(struct wr_iot_restart_restore *s,const char *directory){'
i=parent.index(a);start=i+len(a);cut=parent.index(' unsigned char id[16]={7};',start)
configure=parent[start:cut]
parent=parent[:i]+'void parent_fixture_configure(const char *directory){'+configure+'}\n'+a+'parent_fixture_configure(directory);\n'+parent[cut:]
backend=backend.replace('int main(int argc,char **argv){',r"""
#include "restart-resume.c"
void parent_fixture_configure(const char *);
void parent_fixture_guest_down_once(void);
static int run_resume_case(const char *directory,const char *mode){
 assert(candidate_read(NULL,"wr_iot_enable"));reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 physical_fixture_prepare();parent_fixture_configure(directory);
 if(!strcmp(mode,"unclaimed"))parent_fixture_drift(1);
 struct wr_iot_restart_resume pump={0};unsigned char id[16]={7};
 assert(wr_iot_restart_resume_begin(&pump,id,19));
 int finish=!strcmp(mode,"finish"),reached=0,injected=0;
 for(unsigned i=0;i<100;i++){
  if(!finish&&pump.phase==WR_RESUME_REBIND){
   enum wr_iot_start_runner_phase phase=backend.start.phase;
   reached=(!strcmp(mode,"stage")&&phase==WR_IOT_RUN_STAGE)||
    (!strcmp(mode,"network")&&phase==WR_IOT_RUN_NETWORK)||
    (!strcmp(mode,"open")&&phase==WR_IOT_RUN_OPEN)||
    (!strcmp(mode,"commit")&&phase==WR_IOT_RUN_COMMIT&&backend.start.commit.phase==WR_IOT_COMMIT_IDLE)||
    (!strcmp(mode,"committed")&&phase==WR_IOT_RUN_COMMIT&&backend.start.commit.phase==WR_IOT_COMMIT_DNS_COMMITTED)||
    (!strcmp(mode,"uncertain")&&phase==WR_IOT_RUN_UNCERTAIN&&backend.start.commit.phase==WR_IOT_COMMIT_DNS_UNCERTAIN)||
    (!strcmp(mode,"admission_clean")&&phase==WR_IOT_RUN_REJECTED&&!backend.start.admission.admitted)||
    (!strcmp(mode,"admission_retained")&&phase==WR_IOT_RUN_UNCERTAIN&&!backend.start.admission.admitted)||
    (!strcmp(mode,"unclaimed")&&!pump.restore.initial_start_claimed&&!backend.start.owner);
   if(reached&&!strncmp(mode,"admission_",10)){assert(admission_fault_taken);admission_fault_guard(0);}
  }
  if(!finish&&!strcmp(mode,"active")&&pump.phase==WR_RESUME_FINISH)reached=1;
  if(reached)break;
  if(finish&&pump.phase==WR_RESUME_FINISH&&!injected){
   fail_unmask=1;assert(!wr_iot_restart_resume_step(&pump));
   assert(pump.phase==WR_RESUME_FINISH&&initial_restart_retained()&&pump.restore.generation.origin.desired.password[0]);
   fail_unmask=0;injected=1;
  }else if(wr_iot_restart_resume_step(&pump)==1)break;
 }
 if(finish){
  assert(injected&&pump.phase==WR_RESUME_DONE&&wr_iot_restart_resume_step(&pump)==1&&!physical_replays);
  physical_fixture_terminal();assert(!initial_restart_retained()&&backend.phase==WR_IOT_OWNER_ACTIVE);
  assert(pump.initial_receipt.open_token&&wr_iot_rc_initial_restart_postrelease_current(&pump.initial_receipt));
 }else{
  assert(reached);wr_iot_rc_shutdown.pending=SIGTERM;
  struct wr_iot_control_request off={.id="08000000000000000000000000000000",.created=20};
  assert(wr_iot_restart_resume_shutdown(&pump,&off));
  close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  for(unsigned i=0;i<100&&pump.phase!=WR_RESUME_CANCELLED;i++){
   if((pump.phase==WR_RESUME_SHUTDOWN_ROLLBACK||pump.phase==WR_RESUME_SHUTDOWN_CLOSED)&&!injected){
    fail_unmask=1;assert(!wr_iot_restart_resume_step(&pump));
    struct wr_iot_rc_physical_resume retained={0};assert(wr_iot_rc_physical_resume_read(&retained));
    assert((pump.restore.initial_start_claimed?initial_restart_retained():!initial_restart_retained())&&pump.restore.generation.origin.desired.password[0]&&!physical_replays);
    fail_unmask=0;injected=1;
   }else (void)wr_iot_restart_resume_step(&pump);
  }
  assert(injected&&pump.phase==WR_RESUME_CANCELLED&&wr_iot_restart_resume_step(&pump)==-1);
  assert(physical_replays==1&&!initial_restart_retained()&&!backend.start.input.request.password[0]);
  parent_fixture_guest_down_once();physical_fixture_terminal();
 }
 parent_fixture_dispose(&pump.restore);return 0;
}
int main(int argc,char **argv){
""")
a=' assert(argc==2||argc==3);assert(candidate_read(NULL,"wr_iot_enable"));'
assert a in backend
backend=backend.replace(a,' assert(argc==2||argc==3);if(getenv("WR_PHYSICAL_RESUME_TEST"))return run_resume_case(argv[1],getenv("WR_PHYSICAL_RESUME_TEST"));assert(candidate_read(NULL,"wr_iot_enable"));')
'''
anchor='\nwith tempfile.TemporaryDirectory('
assert anchor in source
source=source.replace(anchor,'\n'+inject+anchor,1)
source=source.replace(" physical_public={", " parent_public.update({'parent_fixture_configure','parent_fixture_guest_down_once','wr_iot_restart_restore_begin','wr_iot_restart_restore_step','wr_iot_restart_restore_handoff','wr_iot_restart_restore_preopen_rejected','wr_iot_restart_restore_rebind_current','wr_iot_restart_guest_step'})\n physical_public={",1)
source=source.replace("'wr_iot_rc_physical_take'}", "'wr_iot_rc_physical_take','wr_iot_rc_physical_premain_cancel','wr_iot_rc_physical_prehandoff_cancel'}",1)
anchor=" subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_CANCEL_TEST':'1'})"
assert anchor in source
source=source.replace(anchor,anchor+'''
 for case in ['finish','stage','network','open','commit','committed','uncertain','active','admission_clean','admission_retained','unclaimed']:
  env={**os.environ,'WR_PHYSICAL_RESUME_TEST':case}
  if case=='uncertain':env['WR_INITIAL_UNCERTAIN_CANCEL_TEST']='1'
  if case.startswith('admission_'):env['WR_INITIAL_ADMISSION_CANCEL_TEST']=case.split('_',1)[1]
  subprocess.run([d+'/check',d],check=True,timeout=30,env=env)
''')
source=source.replace("print('PASS actual physical INITIAL", "print('PASS actual resume and Guest controllers plus physical INITIAL")
exec(compile(source,str(Path(__file__)), 'exec'),{'__file__':__file__})
