"""Actual physical session/fence/resume cleanup; finish observations injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
prefix=prefix.replace('int wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){(void)s;return 0;}', 'static int proof_ok;\nint wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){assert(s);return proof_ok;}')
prefix=prefix.replace('int wr_iot_restart_restore_cancel_check(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){(void)s;(void)q;return 0;}', 'static int closed_proof; int wr_iot_restart_restore_cancel_check(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){assert(s&&q);return closed_proof;}')
code=prefix+r'''
static int fail_mask;
static int checked_mask(int op,const sigset_t*set,sigset_t*old){if(op==SIG_SETMASK&&fail_mask)return -1;return sigprocmask(op,set,old);}
#define sigprocmask checked_mask
#include "radio-stop-fence.c"
#undef sigprocmask
static struct wr_iot_restart_restore *observed;
static int cancel_mode;
static void finish_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(observed->phase==(cancel_mode?WR_RESTORE_CANCELLED:WR_RESTORE_FINISHED)&&!observed->generation.profile.active);
 assert(!observed->generation.profile.files.saved[0].data&&!observed->generation.origin.desired.password[0]);
 assert(!observed->multicast.main&&!observed->multicast.guest);
 assert(!physical.quiesce.desired.password[0]&&physical.result==(cancel_mode?-1:1)&&!physical.guard&&!depth);
 shutdowns++;
}
int main(int argc,char **argv){
 (void)argv;cancel_mode=argc==2;
 (void)handler;struct sigaction action={0};action.sa_handler=finish_handler;sigemptyset(&action.sa_mask);assert(!sigaction(SIGTERM,&action,NULL));
 struct wr_iot_rc_physical_intent intent={1,1,1},taken={0};
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=1};
 query_status=WR_STOP_COMPLETE;assert(wr_iot_rc_physical_begin_quiesce(&intent,&off));
 for(int i=0;i<30&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(physical.finishing==1&&physical.guard==1&&depth==1&&wr_iot_rc_shutdown.active);
 struct wr_iot_restart_restore root={0};observed=&root;root.owner=getpid();root.phase=WR_RESTORE_HANDOFF;root.multicast.main=&root.main;root.multicast.guest=&root.guest;
 root.generation.profile.active=1;root.generation.profile.files.count=1;
 root.generation.profile.files.saved[0].data=malloc(8);assert(root.generation.profile.files.saved[0].data);
 root.generation.profile.files.saved[0].size=8;memset(root.generation.profile.files.saved[0].data,'s',8);
 strcpy(root.generation.origin.desired.password,"secret");
 assert(!wr_iot_rc_physical_resume_finish(&root)&&root.generation.profile.active&&depth==1);
 proof_ok=1;fail_mask=1;
 if(cancel_mode)assert(!kill(getpid(),SIGTERM)&&!shutdowns);
 assert(!wr_iot_rc_physical_resume_finish(&root)&&root.generation.profile.active&&root.generation.profile.files.saved[0].data&&depth==1&&!root.busy&&!physical.result);
 fail_mask=0;
 root.iapp=(struct wr_iot_iapp_child){.owner=getpid(),.attempted=1,.fd=-1,.result=-2};
 assert(!wr_iot_rc_physical_resume_finish(&root)&&physical.guard==1);
 root.iapp.result=1;
 if(cancel_mode){
  assert(!wr_iot_rc_physical_resume_finish(&root));
  assert(wr_iot_rc_shutdown.pending==SIGTERM&&root.generation.profile.active&&depth==1&&!shutdowns);
  struct wr_iot_rc_quiesce closed={0};
  assert(!wr_iot_rc_physical_resume_cancel(&root,&closed)&&!shutdowns);
  closed_proof=1;fail_mask=1;
  assert(!wr_iot_rc_physical_resume_cancel(&root,&closed)&&root.generation.profile.active&&depth==1);
  fail_mask=0;assert(wr_iot_rc_physical_resume_cancel(&root,&closed));
 }else assert(wr_iot_rc_physical_resume_finish(&root));
 assert(shutdowns==cancel_mode&&root.phase==(cancel_mode?WR_RESTORE_CANCELLED:WR_RESTORE_FINISHED)&&!wr_iot_rc_shutdown.active&&depth==0);
 assert(!root.main.generation&&!root.guest.main&&!root.services.main);
 assert(!wr_iot_rc_physical_resume_finish(&root)&&shutdowns==cancel_mode);
 assert(wr_iot_rc_physical_take(&taken)==(cancel_mode?-1:1)&&taken.restart);
 assert(!wr_iot_rc_physical_take(&taken));
 puts("PASS actual physical resume/fence cleanup: failed proof/mask retains baseline and guard, normal finish without signal; queued TERM retains until cancellation proof, failed cancel unmask retains, retry wipes credentials before replay, terminal take once; finish evidence/driver/resource actors injected");
}
'''
prepared=code
anchor='static int fail_mask;'
assert prepared.count(anchor)==1
prepared=prepared.replace(anchor,r'''
int wr_iot_service_guard_dup(void){assert(0);return -1;}
static int history_ready=1,history_prepares,history_commits;
int wr_iot_rc_restart_profile_prepare(struct wr_iot_restart_restore*s,struct wr_iot_restart_profile_history*out){
 assert(s&&s->owner==getpid()&&!s->busy&&depth==1&&wr_iot_rc_shutdown.active&&s->generation.profile.active);
 history_prepares++;memset(out,0,sizeof(*out));if(!history_ready)return 0;
 out->binding.kind=WR_PROFILE_BACKEND_REBIND_ACTIVE;out->binding.created=9;return 1;
}
void wr_iot_rc_restart_profile_commit(const struct wr_iot_restart_profile_history*s){
 assert(depth==1&&wr_iot_rc_shutdown.active&&s==&physical.finish_profile&&s->binding.created==9);
 history_commits++;
}
'''+anchor)
prepared=prepared.replace(' strcpy(root.generation.origin.desired.password,"secret");',r'''
 strcpy(root.generation.origin.desired.password,"secret");
 memset(&root.generation.config_revision,0x33,sizeof(root.generation.config_revision));
 memset(&root.generation.provisioning,0x44,sizeof(root.generation.provisioning));
''')
prepared=prepared.replace(' assert(!root.main.generation&&!root.guest.main&&!root.services.main);',r'''
 struct wr_iot_generation_config empty={0};struct wr_iot_saved_config clear={0};
 assert(!memcmp(&root.generation.config_revision,&empty,sizeof(empty))&&
  !memcmp(&root.generation.provisioning,&clear,sizeof(clear)));
 assert(!root.main.generation&&!root.guest.main&&!root.services.main);
''')
anchor=' proof_ok=1;fail_mask=1;'
assert prepared.count(anchor)==1
prepared=prepared.replace(anchor,r'''
 proof_ok=1;history_ready=0;
 assert(!wr_iot_rc_physical_resume_finish(&root)&&root.generation.profile.active&&!history_commits&&depth==1);
 history_ready=1;
'''+anchor)
anchor=' fail_mask=0;\n root.iapp='
assert prepared.count(anchor)==1
prepared=prepared.replace(anchor,' assert(!history_commits&&history_prepares>=2&&physical.finish_profile.binding.created==9);\n'+anchor)
anchor=' assert(shutdowns==cancel_mode&&root.phase=='
assert prepared.count(anchor)==1
prepared=prepared.replace(anchor,' assert(history_commits==!cancel_mode&&!physical.finish_profile.binding.kind);\n'+anchor)

with tempfile.TemporaryDirectory(prefix='wr-resume-finish-') as d:
 p=Path(d)/'test.c';b=Path(d)/'test'
 for mode,source in [(0,code),(1,prepared)]:
  p.write_text(source)
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(mode),'-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),'-o',str(b)],check=True)
  for args in [[],["cancel"]]:subprocess.run([str(b)]+args,check=True,timeout=15)

print('PASS prepared restart publication: preflight/unmask failure holds inert candidate; success commits once; pending TERM cancels without commit; credential revisions wiped in both terminal cleanups')
