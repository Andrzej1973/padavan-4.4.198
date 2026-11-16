from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent;candidate=here/'rc-physical-stop.c'
source=(here/'check-rc-physical-stop.c').read_text();prefix=source.split('int main(void)',1)[0]
begin=prefix.index('/* Legacy fixture rejects INITIAL_OFF admission;')
end=prefix.index('static void handler(int sig)',begin)
prefix=prefix[:begin]+prefix[end:]
prefix=prefix.replace('#include "rc-physical-stop.c"','#include "'+str(candidate)+'"')
prefix=prefix.replace('int wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){(void)s;return 0;}', 'static int initial_finish_proof;\nint wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){assert(s);return initial_finish_proof;}')
prefix=prefix.replace('static int depth,','static int prepared_initial,initial_calls;\nstatic int depth,',1)
prefix=prefix.replace('assert(depth==2&&slot<6&&!calls&&!downs);','assert(depth>=2&&slot<6&&!calls&&!downs);')
prefix=prefix.replace('assert(depth==2&&wr_iot_rc_shutdown.active);downs++','assert(depth>=2&&wr_iot_rc_shutdown.active);downs++')
code=prefix+r'''
#include "physical-initial-session.c"
#include "rc-initial-stop.c"
int wr_iot_activation_prepare_radio_stop(void){assert(depth==1&&wr_iot_rc_shutdown.active);prepared_initial++;return 1;}
int wr_iot_rc_backend_prepared_initial_request(const unsigned char *nonce,struct wr_iot_physical_initial_request *q){
 assert(depth==3&&aux_calls==6&&!downs&&!initial_calls);
 *q=(struct wr_iot_physical_initial_request){.action=WR_STOP_ARM,.epoch=11,.generation=12,.idle_serial=13};memcpy(q->nonce,nonce,16);return 1;
}
enum wr_iot_physical_call_result wr_iot_physical_initial_call(const struct wr_iot_physical_initial_request *q,struct wr_iot_physical_initial_response *out){
 assert(depth==3&&q->idle_serial==13&&q->nonce[0]==7);initial_calls++;
 out->identity=*q;out->identity.attempt=19;
 out->status=q->action==WR_STOP_ARM?WR_STOP_ARMED:q->action==WR_STOP_RELEASE?WR_STOP_RELEASED:WR_STOP_COMPLETE;
 return WR_PHYSICAL_CALL_ACKNOWLEDGED;
}
int main(void){
 (void)handler;
 struct wr_iot_rc_physical_intent intent={1,0,0};struct wr_iot_physical_initial_request released;
 struct wr_iot_rc_physical_resume legacy;
 closed_fail=1; /* No CLOSE: actual ordinary entry must prove initial origin. */
 assert(wr_iot_rc_physical_begin(&intent));assert(prepared_initial==1&&depth==1);
 assert(!wr_iot_rc_physical_begin_initial(&intent));
 for(unsigned i=0;i<20&&physical.finishing!=1;i++)wr_iot_rc_physical_step();
 assert(physical.finishing==1&&downs==1&&aux_calls==6&&initial_calls==3&&depth==1);
 assert(wr_iot_rc_physical_initial_release_read(&released)&&released.action==WR_STOP_RELEASE);
 assert(wr_iot_rc_physical_resume_read(&legacy));
 assert(legacy.origin==WR_PHYSICAL_ORIGIN_INITIAL&&!legacy.physical.action&&
  legacy.initial.action==WR_STOP_RELEASE&&!legacy.resume_needed);
 assert(legacy.initial.epoch==released.epoch&&legacy.initial.attempt==released.attempt);

 assert(physical.owner==getpid()&&physical.guard==1&&wr_iot_rc_shutdown.active);
 int before=initial_calls;wr_iot_rc_physical_step();assert(initial_calls==before&&downs==1);
 struct wr_iot_restart_restore root={0};struct wr_iot_rc_physical_intent taken={0};
 root.owner=getpid();root.phase=WR_RESTORE_PREPARED;
 root.generation.origin.origin=WR_PHYSICAL_ORIGIN_INITIAL;
 root.generation.profile.active=1;root.generation.profile.files.count=1;
 root.generation.profile.files.saved[0].data=malloc(8);assert(root.generation.profile.files.saved[0].data);
 root.generation.profile.files.saved[0].size=8;
 assert(!wr_iot_rc_physical_resume_finish(&root)&&physical.guard&&root.generation.profile.active);
 initial_finish_proof=1;assert(wr_iot_rc_physical_resume_finish(&root));
 assert(root.phase==WR_RESTORE_FINISHED&&!root.generation.profile.active&&!root.generation.profile.files.saved[0].data);
 assert(!physical.guard&&!physical.fence.owner&&!depth&&!wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_physical_resume_finish(&root));
 assert(wr_iot_rc_physical_take(&taken)==1&&taken.restart);

 return 0;
}
'''
ordinary_shutdown_actors = r"""
int wr_iot_rc_boot_idle(void){return 0;}
int wr_iot_rc_backend_initial_shutdown_prepare(const struct wr_iot_control_request *r,const struct wr_iot_initial_shutdown_owner *o){(void)r;(void)o;assert(0);return 0;}
int wr_iot_rc_backend_shutdown_initial_request(const struct wr_iot_initial_shutdown_owner *o,const unsigned char *n,struct wr_iot_physical_initial_request *q){(void)o;(void)n;(void)q;assert(0);return 0;}
"""
code += ordinary_shutdown_actors

with tempfile.TemporaryDirectory(prefix='wr-initial-owner-') as d:
 p=Path(d)/'check.c';p.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
off_main=r'''
int main(void){
 (void)handler;
 struct wr_iot_control_request off={.id="01010101010101010101010101010101",.created=17};
 struct wr_iot_physical_initial_request released;struct wr_iot_physical_stop_request legacy;
 assert(!wr_iot_rc_physical_initial_off_read(off.id,off.created,&released));
 assert(wr_iot_rc_physical_begin_initial_off(&off));
 assert(!wr_iot_rc_physical_initial_off_read(off.id,off.created,&released));
 for(unsigned i=0;i<20&&!physical.result;i++)wr_iot_rc_physical_step();
 assert(physical.result==1&&downs==1&&aux_calls==6&&initial_calls==3&&!depth);
 assert(!physical.guard&&!physical.fence.owner&&!wr_iot_rc_shutdown.active);
 assert(wr_iot_rc_physical_initial_off_read(off.id,off.created,&released)&&released.action==WR_STOP_RELEASE);
 assert(!wr_iot_rc_physical_initial_off_read(off.id,off.created+1,&released)&&!released.action);
 assert(!wr_iot_rc_physical_initial_off_read("02020202020202020202020202020202",off.created,&released));
 assert(!wr_iot_rc_physical_off_read(off.id,off.created,&legacy)&&!legacy.action);
 int before=initial_calls;
 for(unsigned i=0;i<3;i++)assert(wr_iot_rc_physical_initial_off_read(off.id,off.created,&released));
 assert(initial_calls==before&&downs==1);
 assert(wr_iot_rc_physical_take_off(off.id,off.created)==1);
 assert(!wr_iot_rc_physical_initial_off_read(off.id,off.created,&released)&&!released.action);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-owner-off-') as d:
 p=Path(d)/'check.c';p.write_text(code.split('int main(void)',1)[0]+off_main+ordinary_shutdown_actors)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
legacy=source # Original legacy fixture keeps initial-observation refusal actors.
with tempfile.TemporaryDirectory(prefix='wr-initial-owner-legacy-') as d:
 p=Path(d)/'check.c';p.write_text(legacy)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual physical owner + initial controller/session: automatic initial selection and existing guards span auth/AUX/one DOWN/typed RELEASE, tagged initial resume leaves legacy tuple empty, restart owner retained, ordinary OFF exact envelope/fence/read/take verified; injected backend/driver, target/runtime pending')
