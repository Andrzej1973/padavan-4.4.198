"""Actual cold root/parent/profile recovery and real pending shutdown fence."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-cold-on-owner.py').read_text();ns={'__file__':str(here/'check-cold-on-owner.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
body=body.replace('#include "radio-stop-fence.c"',r'''
static int fail_root_unmask;
static int root_mask(int how,const sigset_t*set,sigset_t*old){if(how==SIG_SETMASK&&fail_root_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask root_mask
#include "radio-stop-fence.c"
#undef sigprocmask
''')
body+=r'''
#include "cold-on-root.h"
#include "cold-on-root-recovery.c"
#define UNREACHED1(name,T) int name(T *a){(void)a;assert(0);return 0;}
#define UNREACHED2(name,T,U) int name(T *a,U *b){(void)a;(void)b;assert(0);return 0;}
UNREACHED2(wr_iot_cold_handoff_begin,struct wr_iot_cold_handoff,struct wr_iot_cold_owner)
UNREACHED1(wr_iot_cold_handoff_step,struct wr_iot_cold_handoff)
UNREACHED2(wr_iot_cold_disabled_begin,struct wr_iot_cold_disabled,struct wr_iot_cold_owner)
UNREACHED1(wr_iot_cold_disabled_current,struct wr_iot_cold_disabled)
UNREACHED2(wr_iot_cold_release_begin,struct wr_iot_cold_release,struct wr_iot_cold_handoff)
UNREACHED1(wr_iot_cold_release_current,struct wr_iot_cold_release)
UNREACHED2(wr_iot_cold_disabled_release_begin,struct wr_iot_cold_disabled_release,struct wr_iot_cold_disabled)
UNREACHED1(wr_iot_cold_disabled_release_current,struct wr_iot_cold_disabled_release)
UNREACHED2(wr_iot_rc_cold_parent_release,struct wr_iot_cold_parent_release,struct wr_iot_cold_release)
UNREACHED2(wr_iot_rc_cold_disabled_parent_release,struct wr_iot_cold_disabled_parent_release,struct wr_iot_cold_disabled_release)
UNREACHED2(wr_iot_rc_cold_terminal_begin,struct wr_iot_cold_terminal,struct wr_iot_cold_parent_release)
UNREACHED2(wr_iot_rc_cold_disabled_terminal_begin,struct wr_iot_cold_disabled_terminal,struct wr_iot_cold_disabled_parent_release)
UNREACHED1(wr_iot_rc_cold_terminal_step,struct wr_iot_cold_terminal)
UNREACHED1(wr_iot_rc_cold_disabled_terminal_step,struct wr_iot_cold_disabled_terminal)
UNREACHED1(wr_iot_rc_cold_terminal_retire,struct wr_iot_cold_terminal)
UNREACHED1(wr_iot_rc_cold_disabled_terminal_retire,struct wr_iot_cold_disabled_terminal)
int wr_iot_cold_root_shutdown(struct wr_iot_cold_root*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rc_cold_root_final_shutdown(struct wr_iot_cold_root*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
#include "cold-on-root-signal.c"
#include "cold-on-root.c"

static struct wr_iot_cold_root *signal_root;static int signals;
static void root_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned);
 assert(signal_root&&!signal_root->parent.admission.profile.files.count);
 for(size_t i=0;i<sizeof(signal_root->parent.input.request);i++)assert(!((unsigned char*)&signal_root->parent.input.request)[i]);
 for(size_t i=0;i<sizeof(signal_root->parent.generation.desired);i++)assert(!((unsigned char*)&signal_root->parent.generation.desired)[i]);
 signals++;
}
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct sigaction sa={0};sa.sa_handler=root_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 strcpy(desired.gateway,"192.168.30.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.30.10");strcpy(desired.last,"192.168.30.40");
 for(int enabled=0;enabled<=1;enabled++)for(int stage=0;stage<3;stage++){
  struct wr_iot_cold_root root={0},zero={0};struct wr_iot_control_request input={0};
  down=1;partial=idle_fault=idle_reads=up_calls=generator_calls=attaches=0;membership=1;make_profile();
  FILE*f=fopen(profile_path,"a");assert(f&&fputs("# root baseline\n",f)>=0&&!fclose(f));
  memset(input.id,'0',32);input.id[1]='1';input.created=7;if(enabled)input.request=desired;
  assert(wr_iot_cold_root_begin(&root,&input,1));
  if(stage){assert(!wr_iot_cold_owner_step(&root.parent)&&root.parent.generation.owner==getpid());}
  if(stage==2){assert(!wr_iot_cold_owner_step(&root.parent)&&generator_calls==1);}
  /* Main attempt always bars old-profile recovery, including NOT_SUBMITTED. */
  root.parent.generation.main_may_have_started=1;assert(!wr_iot_cold_root_preup_recover(&root));root.parent.generation.main_may_have_started=0;
  if(stage==2){
   char parked[1100];snprintf(parked,sizeof(parked),"%s/parked",argv[1]);assert(!rename(profile_path,parked));
   f=fopen(profile_path,"w");assert(f&&fputs("foreign inode\n",f)>=0&&!fclose(f));
   assert(!wr_iot_cold_root_preup_recover(&root)&&root.owner&&depth==1&&root.parent.admission.profile.files.count==1);
   char b[64]={0};f=fopen(profile_path,"r");assert(f&&fgets(b,sizeof(b),f)&&!fclose(f)&&!strcmp(b,"foreign inode\n"));
   assert(!unlink(profile_path)&&!rename(parked,profile_path));
  }
  signal_root=&root;signals=0;assert(!raise(SIGTERM)&&!signals);
  fail_root_unmask=1;assert(!wr_iot_cold_root_step(&root)&&root.owner&&depth==1&&!signals);
  assert(root.phase==WR_COLD_ROOT_RETAINED&&root.parent.phase==WR_COLD_OWNER_RETAINED);
  for(size_t i=0;i<sizeof(root.parent.input.request);i++)assert(!((unsigned char*)&root.parent.input.request)[i]);
  assert(!wr_iot_cold_owner_step(&root.parent));
  fail_root_unmask=0;assert(wr_iot_cold_root_step(&root)==-1&&signals==1&&!depth&&!memcmp(&zero,&root,sizeof(root)));
  assert(!up_calls&&generator_calls==(stage==2));
  char b[4096]={0};f=fopen(profile_path,"r");assert(f&&fread(b,1,sizeof(b)-1,f)>0&&!fclose(f)&&strstr(b,"# root baseline\n"));
  assert(!wr_iot_cold_root_preup_recover(&root)&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-root-recovery-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=20)
print('PASS actual cold root pre-UP recovery both intents/capture/generated: foreign inode retained, Main attempt bars rollback, failed unmask retains irrevocable cancellation, real SIGTERM after credential/profile/guard cleanup, baseline restored without generator/Main replay; SDK/DOWN actors')
