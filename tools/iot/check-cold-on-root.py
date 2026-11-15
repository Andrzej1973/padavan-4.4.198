"""Private cold root sequencing; child contracts are explicit injected actors."""
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
static int enabled,admit=1,prepare=1,backend=1,active=1,capture=1,release_ok=1,terminal=1,retire=1;
static int begins,handoffs,disabled_begins,disabled_reads,captures,releases,term_steps,retires;
int wr_iot_cold_owner_begin(struct wr_iot_cold_owner*s,const struct wr_iot_control_request*r,int reload){
 assert(s==&root->parent&&r->request.enabled==enabled&&reload==1);begins++;
 if(!admit)return 0;
 s->owner=getpid();s->phase=admit==2?WR_COLD_OWNER_RETAINED:WR_COLD_OWNER_ADMITTED;return 1;
}
int wr_iot_cold_owner_step(struct wr_iot_cold_owner*s){assert(s==&root->parent);return prepare;}
int wr_iot_cold_handoff_begin(struct wr_iot_cold_handoff*s,struct wr_iot_cold_owner*p){
 assert(enabled&&s==&root->handoff&&p==&root->parent);handoffs++;s->owner=getpid();s->backend_claimed=backend;return 1;
}
int wr_iot_cold_handoff_step(struct wr_iot_cold_handoff*s){assert(enabled&&s==&root->handoff);return active;}
int wr_iot_cold_disabled_begin(struct wr_iot_cold_disabled*s,struct wr_iot_cold_owner*p){
 assert(!enabled&&s==&root->disabled&&p==&root->parent);disabled_begins++;s->owner=getpid();return 0;
}
int wr_iot_cold_disabled_current(struct wr_iot_cold_disabled*s){assert(!enabled&&s==&root->disabled);disabled_reads++;return active;}
int wr_iot_cold_release_begin(struct wr_iot_cold_release*s,struct wr_iot_cold_handoff*h){assert(enabled&&s==&root->release&&h==&root->handoff);captures++;s->owner=getpid();return 0;}
int wr_iot_cold_release_current(struct wr_iot_cold_release*s){assert(enabled&&s==&root->release);return capture;}
int wr_iot_cold_disabled_release_begin(struct wr_iot_cold_disabled_release*s,struct wr_iot_cold_disabled*d){assert(!enabled&&s==&root->disabled_release&&d==&root->disabled);captures++;s->owner=getpid();return 0;}
int wr_iot_cold_disabled_release_current(struct wr_iot_cold_disabled_release*s){assert(!enabled&&s==&root->disabled_release);return capture;}
int wr_iot_rc_cold_parent_release(struct wr_iot_cold_parent_release*s,struct wr_iot_cold_release*r){assert(enabled&&s==&root->released&&r==&root->release);releases++;if(release_ok)s->released=1;return release_ok;}
int wr_iot_rc_cold_disabled_parent_release(struct wr_iot_cold_disabled_parent_release*s,struct wr_iot_cold_disabled_release*r){assert(!enabled&&s==&root->disabled_released&&r==&root->disabled_release);releases++;if(release_ok)s->released=1;return release_ok;}
int wr_iot_rc_cold_terminal_begin(struct wr_iot_cold_terminal*s,struct wr_iot_cold_parent_release*r){assert(enabled&&s==&root->terminal&&r==&root->released&&r->released);s->owner=getpid();return 1;}
int wr_iot_rc_cold_disabled_terminal_begin(struct wr_iot_cold_disabled_terminal*s,struct wr_iot_cold_disabled_parent_release*r){assert(!enabled&&s==&root->disabled_terminal&&r==&root->disabled_released&&r->released);s->owner=getpid();return 1;}
int wr_iot_rc_cold_terminal_step(struct wr_iot_cold_terminal*s){assert(enabled&&s==&root->terminal);term_steps++;return terminal;}
int wr_iot_rc_cold_disabled_terminal_step(struct wr_iot_cold_disabled_terminal*s){assert(!enabled&&s==&root->disabled_terminal);term_steps++;return terminal;}
int wr_iot_rc_cold_terminal_retire(struct wr_iot_cold_terminal*s){assert(enabled&&s==&root->terminal);retires++;return retire;}
int wr_iot_rc_cold_disabled_terminal_retire(struct wr_iot_cold_disabled_terminal*s){assert(!enabled&&s==&root->disabled_terminal);retires++;return retire;}
int main(void){
 struct wr_iot_cold_root state={0},before;struct wr_iot_control_request request={0};root=&state;
 for(enabled=0;enabled<=1;enabled++){
  request.request.enabled=enabled;memset(&state,0,sizeof(state));begins=handoffs=disabled_begins=disabled_reads=captures=releases=term_steps=retires=0;
  admit=0;assert(!wr_iot_cold_root_begin(root,&request,1)&&!root->owner);admit=1;
  assert(wr_iot_cold_root_begin(root,&request,1)&&!wr_iot_cold_root_begin(root,&request,1));
  assert(!wr_iot_cold_root_retire(root));
  before=state;wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_root_step(root)&&!memcmp(&before,&state,sizeof(state)));wr_iot_rc_shutdown.pending=0;
  prepare=0;assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_PREPARE);prepare=1;
  assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_HANDOFF);
  active=0;for(int i=0;i<3;i++)assert(!wr_iot_cold_root_step(root));
  assert(enabled?handoffs==1:disabled_begins==1);active=1;
  assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_CAPTURE);
  capture=0;for(int i=0;i<3;i++)assert(!wr_iot_cold_root_step(root));assert(captures==1);
  capture=1;assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_RELEASE);
  release_ok=0;assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_RELEASE);
  release_ok=1;assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_TERMINAL_BEGIN);
  assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_TERMINAL);
  terminal=0;wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_root_step(root)&&term_steps==1);wr_iot_rc_shutdown.pending=0;
  terminal=1;assert(wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_DONE);
  terminal=0;assert(!wr_iot_cold_root_step(root)); /* DONE is re-observed, not cached. */
  retire=0;before=state;assert(!wr_iot_cold_root_retire(root)&&!memcmp(&before,&state,sizeof(state)));
  retire=1;assert(wr_iot_cold_root_retire(root));memset(&before,0,sizeof(before));assert(!memcmp(&before,&state,sizeof(state)));
 }
 root->stop.phase=WR_COLD_STOP_CLOSED;assert(!wr_iot_cold_root_begin(root,&request,1));memset(root,0,sizeof(*root));
 enabled=1;request.request.enabled=1;admit=2;assert(wr_iot_cold_root_begin(root,&request,1));
 assert(state.phase==WR_COLD_ROOT_RETAINED&&!wr_iot_cold_root_step(root)&&!wr_iot_cold_root_begin(root,&request,1));
 memset(&state,0,sizeof(state));admit=1;backend=0;assert(wr_iot_cold_root_begin(root,&request,1));
 assert(!wr_iot_cold_root_step(root));assert(!wr_iot_cold_root_step(root)&&state.phase==WR_COLD_ROOT_RETAINED);
 int previous=handoffs;for(int i=0;i<3;i++)assert(!wr_iot_cold_root_step(root));assert(handoffs==previous);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-root-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'cold-on-root.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=20)
print('PASS private cold root both intents: stable parent/child addresses, retained admission/backend refusal, captured OFF observer not begun twice, release/terminal proof retries, child drain under pending, fresh DONE and retirement; child actors, public/shutdown routing unbound')
