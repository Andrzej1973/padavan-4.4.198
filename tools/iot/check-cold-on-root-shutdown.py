"""Root shutdown routes existing exact child controllers; child actors injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "cold-on-root.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct wr_iot_cold_root *root;
static int pre_ok,stop_ready,release_ok,begins,steps,releases,pre_calls;
int wr_iot_cold_prehandoff_shutdown(struct wr_iot_cold_owner*p){assert(p==&root->parent);pre_calls++;return pre_ok;}
int wr_iot_cold_postshutdown_begin(struct wr_iot_cold_stop*s,struct wr_iot_cold_owner*p,struct wr_iot_cold_handoff*h,const struct wr_iot_control_request*off){
 assert(s==&root->stop&&p==&root->parent&&h==&root->handoff&&off&&off->created==8);begins++;
 s->owner=getpid();s->parent=p;s->handoff=h;return 1;
}
int wr_iot_cold_postshutdown_step(struct wr_iot_cold_stop*s){assert(s==&root->stop);steps++;return stop_ready;}
int wr_iot_rc_cold_postshutdown_release(struct wr_iot_cold_stop*s){assert(s==&root->stop);releases++;return release_ok;}
static void setup(struct wr_iot_cold_root*s,int enabled,int handoff){
 memset(s,0,sizeof(*s));root=s;s->owner=getpid();s->enabled=enabled;s->phase=WR_COLD_ROOT_WAIT;
 s->parent.owner=getpid();s->parent.generation.main_may_have_started=1;
 if(handoff){s->handoff.owner=getpid();s->handoff.parent=&s->parent;s->handoff.attempted=s->handoff.backend_claimed=1;}
 wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.pending=SIGTERM;
}
int main(void){
 struct wr_iot_cold_root s,before,zero={0};struct wr_iot_control_request off={0};off.created=8;
 for(int enabled=0;enabled<=1;enabled++){
  setup(&s,enabled,0);pre_ok=0;before=s;assert(!wr_iot_cold_root_shutdown(&s,NULL)&&!memcmp(&before,&s,sizeof(s)));
  pre_ok=1;assert(wr_iot_cold_root_shutdown(&s,NULL)&&!memcmp(&zero,&s,sizeof(s)));
 }
 setup(&s,1,1);assert(!wr_iot_cold_root_shutdown(&s,NULL)&&!begins);
 assert(!wr_iot_cold_root_shutdown(&s,&off)&&begins==1&&!steps&&!releases);
 off.created=99;stop_ready=0;assert(!wr_iot_cold_root_shutdown(&s,&off)&&begins==1&&steps==1&&!releases);
 stop_ready=1;release_ok=0;before=s;assert(!wr_iot_cold_root_shutdown(&s,NULL)&&begins==1&&releases==1&&!memcmp(&before,&s,sizeof(s)));
 release_ok=1;assert(wr_iot_cold_root_shutdown(&s,NULL)&&!memcmp(&zero,&s,sizeof(s)));
 for(int fault=0;fault<10;fault++){
  setup(&s,1,1);int old_b=begins,old_s=steps,old_r=releases,old_p=pre_calls;
  switch(fault){
   case 0:s.busy=1;break;case 1:s.parent.owner++;break;case 2:s.parent.generation.main_may_have_started=0;break;
   case 3:s.released.released=1;break;case 4:s.disabled_terminal.owner=getpid();break;
   case 5:wr_iot_rc_shutdown.pending=0;break;case 6:wr_iot_rc_shutdown.radio_on_owned=1;break;
   case 7:s.handoff.parent=NULL;break;case 8:s.enabled=0;break;case 9:s.handoff.backend_claimed=0;break;
  }
  before=s;assert(!wr_iot_cold_root_shutdown(&s,&off)&&!memcmp(&before,&s,sizeof(s)));
  assert(begins==old_b&&steps==old_s&&releases==old_r&&pre_calls==old_p);
 }
 setup(&s,1,1);s.stop.owner=getpid();s.stop.parent=NULL;s.stop.handoff=&s.handoff;
 before=s;assert(!wr_iot_cold_root_shutdown(&s,NULL)&&!memcmp(&before,&s,sizeof(s)));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-root-stop-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'cold-on-root-shutdown.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=20)
print('PASS cold root post-UP shutdown routing: both prehandoff intents, one bound fresh OFF begin, existing stop continuation, release refusal retained, root cleared only after child release, foreign/pre-UP/post-release contexts refused; child actors, no public entry')
