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
#include "cold-on-admission.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,available,mode_ok=1,down=1,reads,drift;
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_service_guard_dup(void){return depth?open("/dev/null",O_RDONLY):-1;}
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request *r){memset(r,0,sizeof(*r));return available;}
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *m){m->router=1;m->radio=mode_ok;m->mode=0;return 1;}
int wr_iot_request_initial_off_current(void){return 1;}
unsigned int if_nametoindex(const char*n){assert(!strcmp(n,"br-iot"));return 0;}
int wr_iot_bss_is_down(void){return down;}
int wr_iot_dns_activation_recovery_state(void){return 0;}
int wr_iot_restart_main_down(void){return down;}
int wr_iot_driver_initial_down_read(const unsigned char*n,struct wr_iot_down_result*r){
 assert(n&&n[0]==1);reads++;*r=(struct wr_iot_down_result){4,2,7};
 if(drift&&reads>2)r->main_close_serial++;
 return 1;
}
#include "precreated-down-observe.c"
#include "cold-on-admission.c"
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
 unsigned char nonce[16]={1};
 for(int fault=0;fault<5;fault++){
  struct wr_iot_cold_admission s={0};reads=0;
  available=fault==1;mode_ok=fault!=2;down=fault!=3;drift=fault==4;
  int claimed=wr_iot_cold_admission_begin(&s,nonce);assert(claimed==(fault!=1&&fault!=2));
  if(claimed){
   assert(depth==1&&wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned);
   assert(s.phase==(fault?WR_COLD_REFUSED:WR_COLD_CAPTURED));
   if(!fault){assert(wr_iot_cold_admission_current(&s));available=1;assert(!wr_iot_cold_admission_current(&s));available=0;
    mode_ok=0;assert(!wr_iot_cold_admission_current(&s));mode_ok=1;
    FILE*f=fopen(profile_path,"w");assert(f&&fputs("foreign profile\n",f)>=0&&!fclose(f));
    assert(!wr_iot_cold_admission_current(&s));
   }
   assert(!wr_iot_cold_admission_begin(&s,nonce));
   if(s.profile.active){s.profile.generated=1;assert(!wr_iot_cold_admission_cancel(&s));s.profile.generated=0;}
   assert(wr_iot_cold_admission_cancel(&s)&&!s.profile.active&&!s.profile.files.count);
   assert(!wr_iot_cold_admission_cancel(&s));
  }
  assert(!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned);
  if(!fault){char buf[64];FILE*f=fopen(profile_path,"r");assert(f&&fgets(buf,sizeof(buf),f)&&!fclose(f)&&!strcmp(buf,"foreign profile\n"));baseline();}
  unchanged();
 }
 /* Actual blocked signal replay must follow credential and guard cleanup. */
 available=drift=reads=0;mode_ok=down=1;
 struct wr_iot_cold_admission pending={0};
 struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,NULL));
 assert(wr_iot_cold_admission_begin(&pending,nonce)&&pending.profile.active);
 assert(!raise(SIGTERM)&&!signals);
 fail_unmask=1;assert(!wr_iot_cold_admission_cancel(&pending)&&pending.profile.active&&depth==1&&wr_iot_rc_shutdown.active&&!signals);
 fail_unmask=0;assert(wr_iot_cold_admission_cancel(&pending)&&signals==1&&!pending.profile.active&&!depth);
 unchanged();
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-admission-') as d:
    p=Path(d)/'check.c'; p.write_text(body); binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(binary)],check=True)
    subprocess.run([str(binary),d],check=True,timeout=15)
print('PASS cold admission: actual profile/fence/observer; historical receipt excluded, DOWN serial drift retained, safe capture cancellation and pending signal cleanup; no Main UP')
