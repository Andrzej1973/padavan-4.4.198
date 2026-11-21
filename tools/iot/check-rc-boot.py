"""Boot readiness + real initial mailbox + canonical RC dispatch/continuation."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <limits.h>
static char directory[PATH_MAX];
#define WR_IOT_CONTROL_DIRECTORY directory
static int fixture_clock(clockid_t,struct timespec*);
#define clock_gettime fixture_clock
#include "control-channel.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
static unsigned long long ticks=100,serial;
static int depth,guard_ok=1,mode_ok=1,mode_radio=1,saved_radio=1,saved_enabled=1,saved_ok=1,policy=1,idle_ready=1,entropy_ok=1,idle_backend=1;
static int entropy_calls,reads,saved_reads,execute_calls,continue_calls,recovery;
static int fixture_clock(clockid_t id,struct timespec*out){assert(id==CLOCK_MONOTONIC);out->tv_sec=(time_t)ticks;out->tv_nsec=0;return 0;}
static int entropy(void*p,unsigned n,unsigned flags){assert(depth==1&&n==32&&flags==1);entropy_calls++;memset(p,0,n);((unsigned char*)p)[0]=1;return entropy_ok?32:31;}
#define WR_IOT_GETRANDOM(b,n,f) entropy(b,n,f)
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);if(!guard_ok)return 0;assert(!depth);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth==1);depth--;}
int wr_iot_rc_boot_idle(void){return idle_backend;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*out){assert(depth);*out=(struct wr_iot_rc_mode){1,mode_radio,0};return mode_ok;}
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode*out){assert(depth);*out=(struct wr_iot_rc_mode){1,saved_radio,0};return mode_ok;}
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request*out){
 assert(depth);saved_reads++;memset(out,0,sizeof(*out));out->enabled=saved_enabled;
 if(saved_enabled){strcpy(out->ssid,"SavedIoT");strcpy(out->password,"iot-password");strcpy(out->gateway,"192.168.30.1");strcpy(out->mask,"255.255.255.0");strcpy(out->first,"192.168.30.10");strcpy(out->last,"192.168.30.40");}
 return saved_ok;
}
int wr_iot_request_initial_off_current(void){assert(depth);return policy;}
unsigned int if_nametoindex(const char*n){assert(depth&&!strcmp(n,"br-iot"));return 0;}
int wr_iot_bss_is_down(void){assert(depth);return 1;}
int wr_iot_dns_activation_recovery_state(void){assert(depth);return 0;}
#include "driver-api-client.h"
int wr_iot_driver_initial_idle_read(const unsigned char*n,struct wr_iot_idle_result*out){assert(depth&&n[0]==1);reads++;*out=(struct wr_iot_idle_result){5,2,++serial};return idle_ready;}
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request*r){
 assert(!depth&&wr_iot_rc_shutdown.active&&r->request.enabled==1&&!strcmp(r->request.ssid,"SavedIoT")&&!strcmp(r->request.password,"iot-password"));
 execute_calls++;return recovery?WR_IOT_RESULT_RECOVERY:WR_IOT_RESULT_APPLIED;
}
enum wr_iot_result_state wr_iot_activation_continue(const char*id,unsigned long long created){assert(wr_iot_rc_shutdown.active&&strlen(id)==32&&created==ticks);continue_calls++;return WR_IOT_RESULT_APPLIED;}
#include "check-mailbox-route-actor.h"
#include "control-server.c"
#include "rc-boot.c"
static void setup(const char*parent,int scenario){
 assert(snprintf(directory,sizeof(directory),"%s/mailbox-%d",parent,scenario)<(int)sizeof(directory));
 boot_armed=boot_spent=0;boot_retry=0;serial=0;
 depth=reads=entropy_calls=saved_reads=execute_calls=continue_calls=recovery=0;
 guard_ok=mode_ok=mode_radio=saved_radio=saved_enabled=saved_ok=policy=idle_ready=entropy_ok=idle_backend=1;
 memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));assert(!wr_iot_rc_boot_pending());wr_iot_rc_boot_arm();assert(wr_iot_rc_boot_pending());
}
int main(int argc,char**argv){
 assert(argc==2);struct wr_iot_mailbox m;struct wr_iot_control_request user={0},claimed={0};struct wr_iot_control_result result;
 setup(argv[1],0);saved_enabled=0;assert(!wr_iot_rc_boot_step()&&!wr_iot_rc_boot_pending()&&!execute_calls&&!entropy_calls&&access(directory,F_OK));
 for(int scenario=1;scenario<=3;scenario++){
  setup(argv[1],scenario);
  if(scenario==2){idle_ready=0;assert(!wr_iot_rc_boot_step()&&wr_iot_rc_boot_pending()&&!execute_calls);int old_reads=reads;assert(!wr_iot_rc_boot_step()&&reads==old_reads);ticks++;idle_ready=1;}
  if(scenario==3){entropy_ok=0;assert(!wr_iot_rc_boot_step()&&wr_iot_rc_boot_pending()&&!execute_calls);ticks++;entropy_ok=1;}
  assert(wr_iot_rc_boot_step()&&!wr_iot_rc_boot_pending()&&!depth&&!execute_calls);
  wr_iot_rc_boot_arm();assert(!wr_iot_rc_boot_pending()&&!wr_iot_rc_boot_step());
  wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,directory,0));assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_QUEUED);wr_iot_mailbox_close(&m);
  if(scenario==3)recovery=1;
  assert(wr_iot_rc_dispatch()&&execute_calls==1);
  if(recovery){assert(wr_iot_rc_pending()&&wr_iot_rc_shutdown.active&&!wr_iot_rc_boot_step());assert(wr_iot_rc_continue()&&continue_calls==1&&!wr_iot_rc_pending());}
  assert(!wr_iot_rc_shutdown.active&&!depth&&!wr_iot_rc_boot_step()&&execute_calls==1);
  char request_path[PATH_MAX];assert(snprintf(request_path,sizeof(request_path),"%s/request",directory)<(int)sizeof(request_path));assert(access(request_path,F_OK));
 }
 for(int scenario=4;scenario<=5;scenario++){
  setup(argv[1],scenario);wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,directory,1));
  memset(&user,0,sizeof(user));memset(user.id,'3',32);user.created=ticks;assert(wr_iot_mailbox_submit(&m,&user));
  if(scenario==5){assert(wr_iot_mailbox_claim(&m,ticks,&claimed));assert(wr_iot_mailbox_finish(&m,user.id,WR_IOT_RESULT_APPLIED,ticks));}
  wr_iot_mailbox_close(&m);assert(!wr_iot_rc_boot_step()&&!wr_iot_rc_boot_pending()&&!execute_calls);
  assert(wr_iot_mailbox_open(&m,directory,0));assert(wr_iot_mailbox_result(&m,&result)&&!strcmp(result.id,user.id)&&result.state==(scenario==4?WR_IOT_RESULT_QUEUED:WR_IOT_RESULT_APPLIED));wr_iot_mailbox_close(&m);
 }
 setup(argv[1],6);idle_backend=0;assert(!wr_iot_rc_boot_step()&&!wr_iot_rc_boot_pending()&&!saved_reads&&!execute_calls);
 setup(argv[1],7);mode_radio=0;assert(!wr_iot_rc_boot_step()&&wr_iot_rc_boot_pending()&&!saved_reads&&!execute_calls);ticks++;mode_radio=1;assert(wr_iot_rc_boot_step());
 setup(argv[1],8);guard_ok=0;assert(!wr_iot_rc_boot_step()&&wr_iot_rc_boot_pending()&&!depth);guard_ok=1;ticks++;assert(wr_iot_rc_boot_step());
 setup(argv[1],10);saved_radio=0;assert(!wr_iot_rc_boot_step()&&!wr_iot_rc_boot_pending()&&!saved_reads&&!execute_calls);
 setup(argv[1],9);wr_iot_rc_shutdown.radio_on_owned=1;assert(!wr_iot_rc_boot_step()&&wr_iot_rc_boot_pending()&&!entropy_calls);wr_iot_rc_shutdown.radio_on_owned=0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-saved-boot-') as d:
 p=Path(d)/'check.c';p.write_text(body);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary),d],check=True,timeout=20)
print('PASS boot saved-ON actual initial mailbox + canonical dispatch/continuation: factory OFF no request, readiness/entropy/guard retry bounded, one publication/execute, preserved user QUEUED/terminal record, recovery owned by normal RC; mode/driver/activation actors, no physical restart')
