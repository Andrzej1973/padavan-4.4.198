"""Actual root post-handoff OFF/REJECTED shutdown, entropy refusal and replay."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-owner.py')}
source=(here/'check-radio-on-owner.py').read_text();exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
other={'__file__':str(here/'check-radio-on-shutdown.py')}
source=(here/'check-radio-on-shutdown.py').read_text();exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],other)
actors=other['body']
a=actors.index('static int closed_ready');b=actors.index('int main(int argc',a)
# This block contains both actual shutdown checks/controller and backend actors.
actors=actors[a:b]
# Avoid duplicated inherited handoff code between the two relevant blocks.
start=actors.index('static int stop_begins')
checks=actors[:actors.index('#include "radio-on-shutdown-check.c"')+len('#include "radio-on-shutdown-check.c"')]
actors=checks+'\n'+actors[start:]
actors=actors.replace('off->created==11','off->created>=10')
body+=actors+r'''
static int finished_signals;
static void root_shutdown_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!on_owner.owner&&!wr_iot_radio_on_pending()&&!depth&&!radio_off_receipt_valid&&!rc_on_shutdown.restore);
 assert(!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned);finished_signals++;
}
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 for(int rejected=0;rejected<2;rejected++){
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=ram_calls=mc_calls=service_calls=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  admitted=active=1;auth_current=wan_current=1;
  struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired};
  assert(wr_iot_rc_radio_on_begin(&r,1));
  for(int tick=0;tick<40&&on_owner.phase!=ON_OWNER_REBIND;tick++)assert(!wr_iot_radio_on_step());
  assert(on_owner.phase==ON_OWNER_REBIND&&ups==1&&on_owner.restore.handoff_created==10);
  struct sigaction sa={0};sa.sa_handler=root_shutdown_signal;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  stop_begins=stop_steps=stop_ready=closed_ready=rejected_ready=allow_stop=0;
  entropy_ready=0;assert(!raise(SIGTERM));int prior=finished_signals;
  assert(!wr_iot_radio_on_step()&&!on_owner.shutdown.owner&&!stop_begins);
  entropy_ready=1;assert(!wr_iot_radio_on_step()&&on_owner.shutdown.owner&&!stop_begins);
  assert(!wr_iot_radio_on_step()&&guest_downs==1&&!stop_begins);
  fail_unmask=1;
  if(rejected)rejected_ready=1;
  else{
   allow_stop=1;assert(!wr_iot_radio_on_step()&&stop_begins==1);
   assert(!wr_iot_radio_on_step()&&stop_steps==1);stop_ready=1;
  }
  assert(!wr_iot_radio_on_step()&&on_owner.owner&&radio_off_receipt_valid&&rc_on_shutdown.restore&&finished_signals==prior);
  assert(stop_begins==!rejected&&ups==1&&on_owner.admission.profile.active);
  fail_unmask=0;assert(wr_iot_radio_on_step()==-1&&finished_signals==prior+1&&!on_owner.owner&&!depth&&!radio_off_receipt_valid);
  assert(stop_begins==!rejected&&ups==1&&generator_calls==1&&!wr_iot_radio_on_pending());
  assert(!unlink(profile_path));
 }
}
'''
prefix=r'''
#define _GNU_SOURCE
#define WR_IOT_FIXTURE_REAL_ON_SHUTDOWN
#define WR_IOT_IAPP_POLICY_H
#define WR_IOT_IAPP_POLICY_PREPARED 1
#include <string.h>
static int entropy_ready;
static long on_stop_entropy(void*b,unsigned n,unsigned f){if(!entropy_ready)return -1;if(n!=32||f!=1)return -1;memset(b,0,n);((unsigned char*)b)[0]=2;return 32;}
#define WR_IOT_GETRANDOM(b,n,f) on_stop_entropy(b,n,f)
'''
with tempfile.TemporaryDirectory(prefix='wr-on-root-shutdown-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(prefix+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual ON root post-handoff shutdown: entropy refusal no mutation, fresh OFF once, Guest drain, CLOSED and REJECTED paths, failed unmask retains root, retry wipes receipt/root before real SIGTERM, no profile rollback/new OPEN; backend actors')
