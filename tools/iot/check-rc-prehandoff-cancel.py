"""Actual physical session/fence/resume cleanup; finish observations injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
prefix=prefix.replace('int wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){(void)s;return 0;}', 'static int proof_ok;\nint wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){assert(s);return proof_ok;}')
prefix=prefix.replace('int wr_iot_restart_restore_cancel_check(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){(void)s;(void)q;return 0;}', 'int wr_iot_restart_restore_cancel_check(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){assert(s&&q);return proof_ok;}')
prefix=prefix.replace('int wr_iot_restart_generation_rollback_current(const struct wr_iot_restart_generation*g){(void)g;return 0;}', 'static int proof_ok;\nint wr_iot_restart_generation_rollback_current(const struct wr_iot_restart_generation*g){assert(g);return proof_ok;}')
prefix=prefix.replace('int wr_iot_restart_prehandoff_cancel_check(struct wr_iot_restart_restore*s){(void)s;return 0;}', 'static int proof_ok;\nint wr_iot_restart_prehandoff_cancel_check(struct wr_iot_restart_restore*s){assert(s);return proof_ok;}')
code=prefix+r'''
static int fail_mask;
static int checked_mask(int op,const sigset_t*set,sigset_t*old){if(op==SIG_SETMASK&&fail_mask)return -1;return sigprocmask(op,set,old);}
#define sigprocmask checked_mask
#include "radio-stop-fence.c"
#undef sigprocmask
static struct wr_iot_restart_restore *observed;
static void finish_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(observed->phase==WR_RESTORE_CANCELLED&&!observed->generation.profile.active);
 assert(!observed->generation.profile.files.saved[0].data&&!observed->generation.origin.desired.password[0]);
 assert(!physical.quiesce.desired.password[0]&&physical.result==-1&&!physical.guard&&!depth);
 shutdowns++;
}
int main(void){
 (void)handler;struct sigaction action={0};action.sa_handler=finish_handler;sigemptyset(&action.sa_mask);assert(!sigaction(SIGTERM,&action,NULL));
 struct wr_iot_rc_physical_intent intent={1,1,1},taken={0};
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=1};
 query_status=WR_STOP_COMPLETE;assert(wr_iot_rc_physical_begin_quiesce(&intent,&off));
 for(int i=0;i<30&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(physical.finishing==1&&physical.guard==1&&depth==1&&wr_iot_rc_shutdown.active);

 struct wr_iot_restart_restore root={0};observed=&root;root.owner=getpid();root.phase=WR_RESTORE_PROFILE;
 root.generation.profile.active=1;root.generation.profile.files.count=1;
 root.generation.profile.files.saved[0].data=malloc(8);assert(root.generation.profile.files.saved[0].data);
 root.generation.profile.files.saved[0].size=8;memset(root.generation.profile.files.saved[0].data,'s',8);
 strcpy(root.generation.origin.desired.password,"secret");
 assert(!wr_iot_rc_physical_prehandoff_cancel(&root)&&root.generation.profile.active&&depth==1);
 proof_ok=1;fail_mask=1;
 assert(!kill(getpid(),SIGTERM)&&!shutdowns);assert(wr_iot_rc_shutdown_note(SIGTERM));
 assert(!wr_iot_rc_physical_prehandoff_cancel(&root)&&root.generation.profile.active&&root.generation.profile.files.saved[0].data&&depth==1&&!root.busy&&!physical.result);
 fail_mask=0;assert(wr_iot_rc_physical_prehandoff_cancel(&root));
 assert(shutdowns==1&&root.phase==WR_RESTORE_CANCELLED&&!wr_iot_rc_shutdown.active&&depth==0);
 assert(!root.main.generation&&!root.guest.main&&!root.services.main);
 assert(!wr_iot_rc_physical_prehandoff_cancel(&root)&&shutdowns==1);
 assert(wr_iot_rc_physical_take(&taken)==-1&&taken.restart);
 assert(!wr_iot_rc_physical_take(&taken));
 puts("PASS actual physical cancellation/fence cleanup: failed proof/mask retains baseline and guard, retry frees private snapshot/wipes credentials before queued SIGTERM replay, terminal take once; finish evidence/driver/resource actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-prehandoff-cancel-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
