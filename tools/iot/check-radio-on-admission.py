"""Exercise actual read-only profile capture and signal fence; no radio UP."""
from pathlib import Path
import subprocess, tempfile
here = Path(__file__).resolve().parent
body = r'''
#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
static char profile_path[1024];
#define WR_IOT_RADIO_PROFILE_PATH profile_path
#include "radio-on-admission.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,available=1,mode_ok=1,down=1,profile_ok=1,receipt_reads,change_receipt,mode_reads,change_mode,profile_reads,change_profile;
static struct wr_iot_physical_stop_request receipt={WR_STOP_RELEASE,1,2,3,4,5,{1}};
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_service_guard_dup(void){return depth?open("/dev/null",O_RDONLY):-1;}
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request *r){receipt_reads++;*r=receipt;if(change_receipt&&receipt_reads>1)r->attempt++;return available;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *m){mode_reads++;m->router=1;m->radio=mode_ok;m->mode=change_mode&&mode_reads>1;return 1;}
int wr_iot_radio_resume_down_observed(const struct wr_iot_physical_stop_request*r){assert(depth&&wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned&&r->action==WR_STOP_RELEASE);return down;}
int wr_iot_rc_off_profile_current(void){profile_reads++;if(change_profile&&profile_reads>1){FILE*f=fopen(profile_path,"w");assert(f&&fputs("foreign profile\n",f)>=0&&!fclose(f));}return profile_ok;}
#include "radio-on-admission.c"
static int fail_unmask,signals;
static int mask_hook(int how,const sigset_t *set,sigset_t *old){if(how==SIG_SETMASK&&fail_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask mask_hook
#include "radio-stop-fence.c"
#undef sigprocmask
static void shutdown_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned);signals++;
}
static void baseline(void){FILE*f=fopen(profile_path,"w");assert(f&&fputs("unchanged baseline\n",f)>=0&&!fclose(f));}
static void unchanged(void){char b[64]={0};FILE*f=fopen(profile_path,"r");assert(f&&fgets(b,sizeof(b),f)&&!fclose(f)&&!strcmp(b,"unchanged baseline\n"));}
int main(int argc,char**argv){
 assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);baseline();
 for(int fault=0;fault<8;fault++){
  struct wr_iot_on_admission s={0};receipt_reads=mode_reads=profile_reads=0;
  available=fault!=1;mode_ok=fault!=2;down=fault!=3;profile_ok=fault!=4;change_receipt=fault==5;change_mode=fault==6;change_profile=fault==7;
  int claimed=wr_iot_on_admission_begin(&s);assert(claimed==(fault!=1&&fault!=2));
  if(claimed){
   assert(depth==1&&wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned);
   assert(s.phase==(fault?WR_ON_ADMISSION_REFUSED:WR_ON_ADMISSION_CAPTURED));
   assert(!wr_iot_on_admission_begin(&s));
   if(s.profile.active){s.profile.generated=1;assert(!wr_iot_on_admission_cancel(&s));s.profile.generated=0;}
   assert(wr_iot_on_admission_cancel(&s)&&!s.profile.active&&!s.profile.files.count);
   assert(!wr_iot_on_admission_cancel(&s));
  }
  assert(!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned);if(fault==7){char b[64];FILE*f=fopen(profile_path,"r");assert(f&&fgets(b,sizeof(b),f)&&!fclose(f)&&!strcmp(b,"foreign profile\n"));baseline();}unchanged();
 }
 /* Actual blocked signal replay must follow credential and guard cleanup. */
 available=mode_ok=down=profile_ok=1;change_receipt=change_mode=change_profile=0;
 struct wr_iot_on_admission pending={0};
 struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,NULL));
 assert(wr_iot_on_admission_begin(&pending)&&pending.profile.active);
 assert(!raise(SIGTERM)&&!signals);
 fail_unmask=1;assert(!wr_iot_on_admission_cancel(&pending)&&pending.profile.active&&depth==1&&wr_iot_rc_shutdown.active&&!signals);
 fail_unmask=0;assert(wr_iot_on_admission_cancel(&pending)&&signals==1&&!pending.profile.active&&!depth);
 unchanged();
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-admission-') as d:
    p=Path(d)/'check.c'; p.write_text(body); binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(binary)],check=True)
    subprocess.run([str(binary),d],check=True,timeout=15)
print('PASS ON admission: actual capture/fence/cancel, absent receipt and mode refusal, stale receipt/DOWN/profile/mode drift retained, generated baseline cannot cancel, original bytes unchanged; no Main UP or RC binding')
