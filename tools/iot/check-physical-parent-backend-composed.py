from pathlib import Path
import subprocess,tempfile,sys,re
root=Path(__file__).resolve().parent;here=Path(__file__).resolve().parent
def setup(name):
 p=root/name;s=p.read_text();ns={'__file__':str(p)};exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<'+name+'>','exec'),ns);return ns
ns=setup('check-parent-backend-composed.py');pn=setup('check-initial-saved-physical.py')
parent=ns['parent'];backend=ns['backend'];prefix=ns['prefix']
# All contexts share the same actual physical origin and service-guard depth.
parent=re.sub(r'^int wr_iot_rc_physical_resume_read\([^\n]*\n','',parent,flags=re.M)
a=' strcpy(saved_enabled,"1");char before[4096];';assert a in parent
parent=parent.replace(a,' assert(wr_iot_rc_physical_resume_read(&origin));(void)origin_reads;(void)fail_origin_at;\n'+a)
backend+='\nint physical_shared_guard_depth(void){return depth;}\n'
physical=pn['code'].split('int main(int argc',1)[0]
physical=physical.replace('struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;','extern struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;')
physical=physical.replace('static int depth,','int physical_shared_guard_depth(void);\n#define depth physical_shared_guard_depth()\nstatic int ',1)
def remove_function(src,name):
 m=re.search(r'^(?:static )?(?:int|void) '+re.escape(name)+r'\(',src,re.M);assert m,name
 start=src.index('{',m.start());level=1;i=start+1
 while level:
  if src[i]=='{':level+=1
  elif src[i]=='}':level-=1
  i+=1
 return src[:m.start()]+src[i:]
for name in ['wr_iot_service_guard_enter','wr_iot_service_guard_leave','wr_iot_restart_restore_finish_check','wr_iot_restart_restore_cancel_check','wr_iot_restart_generation_rollback_current']:
 physical=remove_function(physical,name)
physical=physical.replace('.epoch=11,.generation=12,.idle_serial=13','.epoch=1,.generation=2,.idle_serial=3').replace('q->idle_serial==13','q->idle_serial==3').replace('out->identity.attempt=19','out->identity.attempt=4')
physical=physical.replace('strcpy(out->ssid,"saved IoT");strcpy(out->password,"fixture-secret-only");','*out=(struct wr_iot_request){.enabled=1,.ssid="IoT",.password="iot-password",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"};')
physical+=r'''
void physical_fixture_prepare(void){
 (void)handler;(void)initial_finish_proof;(void)guard_fail;
 struct wr_iot_rc_physical_intent intent={1,1,1};
 assert(!depth&&!wr_iot_rc_shutdown.active);
 assert(wr_iot_rc_physical_begin_initial_saved(&intent));
 for(unsigned i=0;i<20&&physical.finishing!=1;i++)wr_iot_rc_physical_step();
 assert(physical.finishing==1&&physical.initial_saved&&depth==1&&downs==1&&initial_calls==3);
}
void physical_fixture_terminal(void){
 assert(!physical.owner&&!physical.guard&&!physical.initial_saved&&!depth&&!wr_iot_rc_shutdown.active);
 assert(downs==1&&initial_calls==3);
}
'''
a=' wr_iot_rc_shutdown.active=1;struct wr_iot_restart_restore parent={0};parent_fixture_prepare(&parent,argv[1]);';assert a in backend
backend=backend.replace(a,' wr_iot_rc_shutdown.active=0;physical_fixture_prepare();struct wr_iot_restart_restore parent={0};parent_fixture_prepare(&parent,argv[1]);')
backend='void physical_fixture_prepare(void);void physical_fixture_terminal(void);\n'+backend
# Real signal replay is observed; injected unmask failure must keep every owner.
backend=backend.replace('int main(int argc,char **argv){',r'''
static volatile sig_atomic_t physical_replays;
static int fail_unmask;
int physical_sigmask(int how,const sigset_t *set,sigset_t *old){
 if(how==SIG_SETMASK&&fail_unmask){errno=EIO;return -1;}
 return sigprocmask(how,set,old);
}
static void physical_replay_handler(int sig){
 if(!wr_iot_rc_shutdown_note(sig)){assert(!depth&&!wr_iot_rc_shutdown.active);physical_replays++;}
}
static void cancel_physical_checked(struct wr_iot_restart_restore *s,const struct wr_iot_rc_quiesce *q){
 struct wr_iot_activation_owner before=backend;int retained_binding=initial_restart_retained();fail_unmask=1;
 assert(!wr_iot_rc_physical_resume_cancel(s,q)&&initial_restart_retained()==retained_binding&&s->phase==WR_RESTORE_HANDOFF);
 assert(!memcmp(&before,&backend,sizeof(before))&&s->generation.origin.desired.password[0]&&!physical_replays);
 fail_unmask=0;assert(wr_iot_rc_physical_resume_cancel(s,q));
 assert(s->phase==WR_RESTORE_CANCELLED&&!initial_restart_retained()&&!s->generation.origin.desired.password[0]);
 assert(!backend.start.input.request.password[0]&&physical_replays==1);
 struct wr_iot_rc_physical_intent taken={0};assert(wr_iot_rc_physical_take(&taken)==-1&&taken.restart);
 physical_fixture_terminal();assert(!wr_iot_rc_physical_take(&taken));
}
int main(int argc,char **argv){
 assert(signal(SIGTERM,physical_replay_handler)!=SIG_ERR);
#ifdef SIGQUIT
 assert(signal(SIGQUIT,physical_replay_handler)!=SIG_ERR);
#endif
''')
a='wr_iot_rc_initial_restart_detach_commit();assert(!initial_restart_retained()&&!backend.start.input.request.password[0]);'
assert backend.count(a)==3;backend=backend.replace(a,'cancel_physical_checked(&parent,NULL);')
a='parent.busy=0;parent_fixture_closed_cancel_check(&parent,&q);'
assert a in backend;backend=backend.replace(a,a+'cancel_physical_checked(&parent,&q);')

# Initial composition currently exercises successful finish, not simulated-root negative processes.
a=' assert(wr_iot_restart_restore_finish_check(&parent));\n assert(wr_iot_restart_initial_active_current(&parent));\n parent_fixture_dispose(&parent);return 0;';assert a in backend
backend=backend.replace(a,r'''
 assert(wr_iot_restart_restore_finish_check(&parent));
 assert(wr_iot_restart_initial_active_current(&parent));
 struct wr_iot_initial_restart_receipt receipt={0};parent.busy=1;
 assert(wr_iot_rc_initial_restart_receipt(&parent,&input,&receipt));parent.busy=0;
 struct wr_iot_activation_owner retained_active=backend;fail_unmask=1;
 assert(!wr_iot_rc_physical_resume_finish(&parent)&&initial_restart_retained()&&parent.generation.origin.desired.password[0]);
 assert(!memcmp(&retained_active,&backend,sizeof(backend)));fail_unmask=0;
 assert(wr_iot_rc_physical_resume_finish(&parent)&&parent.phase==WR_RESTORE_FINISHED);
 assert(!initial_restart_retained()&&!parent.generation.origin.desired.password[0]);
 assert(backend.phase==WR_IOT_OWNER_ACTIVE&&backend.start.input.request.password[0]);
 struct wr_iot_rc_physical_intent taken={0};assert(wr_iot_rc_physical_take(&taken)==1&&taken.restart);
 physical_fixture_terminal();assert(wr_iot_rc_initial_restart_postrelease_current(&receipt));
 assert(!wr_iot_rc_physical_take(&taken));
 parent_fixture_dispose(&parent);return 0;
''')
with tempfile.TemporaryDirectory(prefix='wr-physical-parent-backend-') as d:
 p=Path(d);subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 (p/'rc.h').write_text((p/'rc.h').read_text()+'\nconst char *nvram_safe_get(const char *);\n')
 (p/'parent.c').write_text(parent);(p/'backend.c').write_text(prefix+'\n#include "check-reopen-unused.h"\n'+backend);(p/'physical.c').write_text(physical)
 flags=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(root)]
 parent_public={'wr_iot_restart_initial_enabled_profile_current','wr_iot_restart_main_bridge_current','parent_fixture_prepare','parent_fixture_drift','parent_fixture_dispose','parent_fixture_cancel_check','parent_fixture_closed_cancel_check','wr_iot_restart_initial_parent_current','wr_iot_restart_initial_handoff_begin','wr_iot_restart_initial_handoff_step','wr_iot_restart_initial_active_current','wr_iot_restart_initial_cancel_step','wr_iot_restart_initial_shutdown_step','wr_iot_restart_restore_finish_check','wr_iot_restart_restore_cancel_check','wr_iot_restart_generation_origin_current','wr_iot_restart_generation_rollback_current'}
 physical_public={'wr_iot_physical_stop_call','wr_iot_physical_stop_down','physical_fixture_prepare','physical_fixture_terminal','wr_iot_rc_physical_resume_read','wr_iot_rc_physical_resume_finish','wr_iot_rc_physical_resume_cancel','wr_iot_rc_physical_take'}
 objects=[]
 for name,public in [('parent',parent_public),('physical',physical_public)]:
  subprocess.run(flags+['-c',str(p/(name+'.c')),'-o',d+'/'+name+'-inventory.o'],check=True)
  symbols=subprocess.check_output(['nm','--defined-only',d+'/'+name+'-inventory.o'],text=True)
  renames=['-D'+line.split()[2]+'='+name+'_fixture_'+line.split()[2] for line in symbols.splitlines() if len(line.split())==3 and line.split()[1]=='T' and line.split()[2] not in public]
  subprocess.run(flags+renames+['-c',str(p/(name+'.c')),'-o',d+'/'+name+'.o'],check=True);objects.append(d+'/'+name+'.o')
 units=p/'units';units.mkdir();compile_units=[]
 for n in [*ns['bn']['units'],'start-commit.c','physical-stop-session.c','radio-stop-fence.c']:
  source=(root if n in ('start-runner.c','start-closed-rollback.c','radio-stop-fence.c') else here)/n
  f=units/n;content=source.read_text()
  if n=='radio-stop-fence.c':content=content.replace('#include <unistd.h>','#include <unistd.h>\nint physical_sigmask(int,const sigset_t *,sigset_t *);\n#define sigprocmask physical_sigmask')
  f.write_text(content);compile_units.append(str(f))
 subprocess.run(flags+[str(p/'backend.c'),*compile_units,*objects,'-o',d+'/check'],check=True)
 subprocess.run([d+'/check',d],check=True,timeout=30)
 import os
 for case in ['STAGE','NETWORK','COMMIT','COMMITTED','UNCERTAIN','OFF']:
  subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_'+case+'_CANCEL_TEST' if case!='OFF' else 'WR_INITIAL_OFF_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_CANCEL_TEST':'1'})
 for kind in ['clean','retained']:
  subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_ADMISSION_CANCEL_TEST':kind})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_UNCLAIMED_CANCEL_TEST':'1'})
print('PASS actual physical INITIAL owner/controller/session/fence plus actual parent/generation/Main/backend/runner/commit/finish/cleanup/postrelease observer: shared shutdown and guard, typed RELEASE origin, one DOWN, credentials wiped at cleanup, ACTIVE retained; hardware/network/DNS/Guest adapters actors, no device proof')
