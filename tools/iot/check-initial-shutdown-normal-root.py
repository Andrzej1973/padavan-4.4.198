from pathlib import Path
import subprocess,tempfile,json,hashlib,datetime
here=Path(__file__).resolve().parent;root=here
script=(root/'check-initial-shutdown-composed.py').read_text();ns={'__file__':str(root/'check-initial-shutdown-composed.py')}
exec(compile(script[:script.index('\nwith tempfile.TemporaryDirectory(')],'<composed prototype setup>','exec'),ns)
# This fixture binds the actual normal controller, not the CLOSE-only actor.
actor='int wr_iot_rc_normal_shutdown_arm_ready(void){assert(0);return 0;}'
assert ns['body'].count(actor)==1
ns['body']=ns['body'].replace(actor,'',1).replace('#include "check-mailbox-normal-consumer.h"','')
body=ns['body'].split('static unsigned initial_stock,initial_private;',1)[0]+r'''
#include "rc-normal-shutdown.c"
#include "cold-on-root.h"
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
static int wr_iot_cold_followup_active(const struct wr_iot_cold_release *r){(void)r;assert(0);return 0;}
int wr_iot_restart_disabled_profile_current(void){return 1;}
int wr_iot_cold_policy_current(const struct wr_iot_cold_policy *p){assert(p);return 1;}
#include "rc-cold-disabled-release.inc"
#include "rc-cold-disabled-followup.inc"
#include "rc-cold-route-handoff.inc"
static unsigned normal_stock;
static void normal_original(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&!wr_iot_rc_shutdown.active);
 assert(normal_shutdown.spent&&!normal_shutdown.owner&&!wr_iot_rc_shutdown.normal_route_armed);
 normal_stock++;
}
int main(int argc,char **argv){
 reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 struct sigaction a={0};a.sa_handler=normal_original;sigemptyset(&a.sa_mask);
 assert(!sigaction(SIGTERM,&a,0)&&!sigaction(SIGQUIT,&a,0));
 struct wr_iot_cold_root cold={0};
 if(argc>1){
  struct wr_iot_control_request cold_off={.id="01020202020202020202020202020202",.created=7};
  struct wr_iot_cold_disabled_release *r=&cold.disabled_release;
  assert(wr_iot_rc_shutdown_begin());
  assert(wr_iot_initial_off_begin(&backend.initial_off,&cold_off));
  backend.owner=getpid();backend.phase=WR_IOT_OWNER_INITIAL_OFF;
  cold.owner=getpid();cold.phase=WR_COLD_ROOT_TERMINAL_BEGIN;
  r->owner=getpid();r->created=cold_off.created;
  r->profile.valid=1;r->profile.owner=getpid();
  assert(snprintf(r->profile.path,sizeof(r->profile.path),"%s/absent-profile",argv[1])>0);
  memcpy(r->id,cold_off.id,sizeof(r->id));
  r->identity.adapter_epoch=backend.initial_off.idle.epoch;
  r->identity.device_generation=backend.initial_off.idle.generation;
  cold.disabled_released.release=r;cold.disabled_released.released=1;
  if(argc>2){
   struct wr_iot_cold_disabled_terminal *t=&cold.disabled_terminal;
   cold.phase=WR_COLD_ROOT_TERMINAL;
   t->owner=getpid();t->parent_release=&cold.disabled_released;
   t->phase=WR_COLD_DISABLED_TERM_RETAINED;t->led_attempted=1;
   r->wan.attempted=r->wan.returned=1;
   if(!strcmp(argv[2],"iapp")){
    t->led_returned=1;t->terminal.owner=getpid();t->terminal.attempted=1;
    t->terminal.result=-1;t->child.owner=getpid();t->child.attempted=1;
    t->child.fd=9;t->child.result=-1;
   }
  }
  assert(!wr_iot_rc_shutdown_end());wr_iot_rc_shutdown.radio_on_owned=1;
 }
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 if(argc>1){
  assert(!wr_iot_rc_normal_shutdown_step()&&!physical.owner&&cold.owner);
  if(argc>2&&!strcmp(argv[2],"iapp")){
   struct wr_iot_cold_disabled_terminal *t=&cold.disabled_terminal;
   assert(!wr_iot_rc_cold_root_routed_handoff(&cold)&&cold.owner);
   t->child.fd=-1;t->child.result=-2;
   assert(!wr_iot_rc_cold_root_routed_handoff(&cold)&&cold.owner);
   t->child.result=-1;t->terminal.shutdown_held=1;
   assert(!wr_iot_rc_cold_root_routed_handoff(&cold)&&cold.owner);
   t->terminal.shutdown_held=0;
  }
  assert(wr_iot_rc_cold_root_routed_handoff(&cold)&&!cold.owner);
  assert(backend.phase==WR_IOT_OWNER_INITIAL_OFF&&backend.initial_off.created==7);
 }
 assert(wr_iot_rc_normal_shutdown_pending());
 assert(!wr_iot_rc_normal_shutdown_step());
 assert(normal_shutdown.claimed&&physical.initial.owner==getpid()&&!normal_stock);
 assert(!raise(SIGQUIT));
 for(unsigned i=0;i<40&&!normal_stock;i++)(void)wr_iot_rc_normal_shutdown_step();
 assert(normal_stock==1&&normal_shutdown.spent&&!normal_shutdown.owner);
 assert(!physical.owner&&!depth&&physical_downs==1&&physical_aux==6&&initial_calls==3);
 assert(!wr_iot_rc_normal_shutdown_pending());
 for(unsigned i=0;i<3;i++)assert(!wr_iot_rc_normal_shutdown_step());
 assert(normal_stock==1&&physical_downs==1&&initial_calls==3);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-normal-root-') as d:
 subprocess.run(['python3',str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d)/'check.c';p.write_text(ns['ns']['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 sources=[str(root/n) if n=='initial-off.c' else str(here/n) for n in ns['ns']['units']]
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+d,'-I'+str(here),str(p),*sources,str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
 subprocess.run([d+'/check',d],check=True,timeout=15)
 for refusal in ('led','iapp'):
  subprocess.run([d+'/check',d,refusal],check=True,timeout=15)
print('PASS empty and cold-disabled INITIAL route through backend, physical RELEASE and one final OS signal: check-initial-shutdown-normal-root.py; external adapters injected, target/runtime pending')
