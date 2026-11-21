"""Actual saved entry, NVRAM adapter, root, restore, release and followup."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-owner.py')}
exec((here/'check-radio-on-owner.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
a='const char *v=!strcmp(key,"wr_iot_enable")?saved_enabled:!strcmp(key,"wr_iot_ssid")?saved_ssid:saved_password;'
b='const char *v=!strcmp(key,"wr_iot_gateway")?"192.168.50.1":!strcmp(key,"wr_iot_mask")?"255.255.255.0":!strcmp(key,"wr_iot_start")?"192.168.50.20":!strcmp(key,"wr_iot_end")?"192.168.50.200":!strcmp(key,"wr_iot_enable")?saved_enabled:!strcmp(key,"wr_iot_ssid")?saved_ssid:saved_password;'
assert body.count(a)==1
body=body.replace(a,b)
prefix='''#define _GNU_SOURCE
#include <time.h>
static int entry_entropy(void *,unsigned,unsigned);
#define WR_IOT_GETRANDOM(b,n,f) entry_entropy(b,n,f)
static int entry_clock(clockid_t,struct timespec *);
#define clock_gettime entry_clock
'''
body+=r'''
int wr_iot_rc_radio_off_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}
#include "restart-entry.h"
enum wr_iot_radio_entry_result wr_iot_cold_on_entry(int on,int reload){(void)on;(void)reload;return WR_RADIO_ENTRY_NATIVE;}
#include "restart-entry.c"
static int entry_entropy(void*b,unsigned n,unsigned f){assert(n==32&&f==1);memset(b,0,n);((unsigned char*)b)[0]=1;return 32;}
static int entry_clock(clockid_t id,struct timespec*out){assert(id==CLOCK_MONOTONIC);out->tv_sec=10;out->tv_nsec=0;return 0;}
int wr_iot_rc_restart_owned(void){assert(0);return 0;}
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent*i,const struct wr_iot_control_request*r){(void)i;(void)r;assert(0);return 0;}
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int enabled=0;enabled<2;enabled++){
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  saved_enabled[0]=enabled?'1':'0';make_profile();
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=ram_fail=mc_fail=0;ram_calls=mc_calls=service_calls=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  auth_current=wan_current=network_current=admitted=active=1;wan_submits=led_calls=child_begins=child_steps=child_failure=child_unknown=begins=continues=0;
  assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_OWNED&&on_owner.iot_enabled==enabled);
  assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED);
  int done=0;for(int tick=0;tick<60&&!done;tick++)done=wr_iot_radio_on_step();
  assert(done==1&&ups==1&&generator_calls==1&&wan_submits==1&&child_begins==1&&begins==enabled);
  assert(wr_iot_radio_on_retire()&&!wr_iot_radio_on_pending());
  assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_NATIVE);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-entry-root-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(prefix+'#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual saved entry + root ON/OFF: copied NVRAM, one Main/WAN/IAPP, duplicate refuses, fresh retirement, only enabled1 rebinds, no receipt returns native; entropy/clock/driver/SDK actors')
