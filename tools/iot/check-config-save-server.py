#!/usr/bin/env python3
"""Actual RC facade routing/receipt gates, owner boundary explicitly modeled."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
body=r'''
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "config-save-server.h"
#include "config-save-owner.h"
static struct wr_iot_save_backend_hooks hooks;
static int registrations,begins,steps,terminals,observes,retires,allow=1;
static enum wr_iot_config_save_phase next=WR_IOT_CONFIG_SAVE_FLASH;
int wr_iot_rc_register_save_backend(const struct wr_iot_save_backend_hooks *h){registrations++;hooks=*h;return registrations==1;}
int wr_iot_config_save_begin_admitted(struct wr_iot_config_save_owner *s,const char *id,unsigned long long t,
 enum wr_iot_flash_save_mode mode,const struct wr_iot_saved_config *config){
 begins++;assert(config->profile.password[0]&&(mode==1||mode==2));
 s->owner=getpid();s->self=(uintptr_t)s;strcpy(s->id,id);s->created=t;s->mode=mode;s->phase=WR_IOT_CONFIG_SAVE_STORING;return 1;
}
enum wr_iot_config_save_phase wr_iot_config_save_step(struct wr_iot_config_save_owner *s,const char *id,unsigned long long t,int cancel){
 steps++;assert(!strcmp(s->id,id)&&s->created==t&&!cancel);s->phase=s->decision=next;return next;
}
int wr_iot_config_save_terminal_ready(struct wr_iot_config_save_owner *s,const char *id,unsigned long long t){
 terminals++;assert(!strcmp(s->id,id)&&s->created==t);if(allow)s->finished=1;return allow;
}
int wr_iot_config_save_observed(struct wr_iot_config_save_owner *s,const char *id,unsigned long long t){observes++;return allow&&s->finished&&!strcmp(s->id,id)&&s->created==t;}
int wr_iot_config_save_retire(struct wr_iot_config_save_owner *s){retires++;if(!s->finished)return 0;memset(s,0,sizeof(*s));return 1;}
int main(void){
 struct wr_iot_control_request request={.id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",.created=9,.operation=WR_IOT_OPERATION_CONFIG_SAVE_AUTO};
 struct wr_iot_control_result result={.id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",.created=9,.state=WR_IOT_RESULT_SAVED_FLASH};
 strcpy(request.request.password,"password123");
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 0
 assert(!wr_iot_rc_save_backend_install()&&!registrations);return 0;
#endif
 assert(wr_iot_rc_save_backend_install()&&registrations==1);
 assert(!wr_iot_rc_save_observed(&result));
 assert(hooks.execute(&request)==WR_IOT_RESULT_RECOVERY&&begins==1);
 assert(hooks.execute(&request)==WR_IOT_RESULT_RECOVERY&&begins==1&&retires==1);
 assert(hooks.progress(request.id,9)==WR_IOT_RESULT_SAVED_FLASH&&steps==1);
 result.state=WR_IOT_RESULT_STORED_RAM;assert(!hooks.terminal(&result)&&!terminals);
 result.state=WR_IOT_RESULT_SAVED_FLASH;allow=0;assert(!hooks.terminal(&result)&&terminals==1);
 allow=1;assert(hooks.terminal(&result)&&hooks.terminal(&result)&&begins==1&&steps==1);
 assert(wr_iot_rc_save_observed(&result));result.created=10;assert(!wr_iot_rc_save_observed(&result));result.created=9;
 allow=0;assert(!wr_iot_rc_save_observed(&result));allow=1;
 next=WR_IOT_CONFIG_SAVE_RAM_ONLY;request.operation=WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT;
 assert(hooks.execute(&request)==WR_IOT_RESULT_RECOVERY&&begins==2);
 assert(hooks.progress(request.id,9)==WR_IOT_RESULT_STORED_RAM);
 assert(!hooks.terminal(&result));result.state=WR_IOT_RESULT_STORED_RAM;
 assert(hooks.terminal(&result)&&wr_iot_rc_save_observed(&result));
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-save-server-') as d:
 p=Path(d)/'check.c';p.write_text(body);binary=Path(d)/'check'
 for enabled in (0,1):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
   '-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED='+str(enabled),'-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-I'+str(here),
   str(p),str(here/'config-save-server.c'),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual Save facade: capability0/1 registration, retained owner, distinct RAM/flash terminal and observation gates, publication retries without replay; owner modeled')
