#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "rc-initial-stop.h"
#include "rc-shutdown-admission.h"
#include "physical-stop-down.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,aux,calls,downs,fail_observe,uncertain,no_submit;static unsigned status=WR_STOP_RUNNING;
int wr_iot_service_guard_enter(int enabled){assert(enabled&&wr_iot_rc_shutdown.active);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth==1);depth--;}
int wr_iot_auth_stop_begin(struct wr_iot_auth_stop *s,unsigned long long now){assert(depth&&now);s->owner=getpid();return 1;}
int wr_iot_auth_stop_step(struct wr_iot_auth_stop *s,unsigned long long now){assert(depth&&now&&s->owner==getpid());return 1;}
int wr_iot_rc_physical_aux_down(unsigned slot){assert(depth&&slot==(unsigned)aux&&!calls&&!downs);aux++;return 1;}
int wr_iot_rc_backend_prepared_initial_request(const unsigned char *nonce,struct wr_iot_physical_initial_request *out){
 assert(depth&&aux==6&&!calls&&!downs);if(fail_observe)return 0;
 *out=(struct wr_iot_physical_initial_request){.action=WR_STOP_ARM,.epoch=1,.generation=2,.idle_serial=5};memcpy(out->nonce,nonce,16);return 1;
}
enum wr_iot_physical_call_result wr_iot_physical_initial_call(const struct wr_iot_physical_initial_request *q,struct wr_iot_physical_initial_response *out){
 assert(depth&&aux==6);calls++;if(uncertain)return WR_PHYSICAL_CALL_UNCERTAIN;
 out->identity=*q;out->identity.attempt=7;out->status=q->action==WR_STOP_ARM?WR_STOP_ARMED:q->action==WR_STOP_RELEASE?WR_STOP_RELEASED:q->action==WR_STOP_CANCEL?WR_STOP_CANCELLED:status;return WR_PHYSICAL_CALL_ACKNOWLEDGED;
}
enum wr_iot_physical_down_result wr_iot_physical_stop_down(void){assert(depth);downs++;return no_submit?WR_PHYSICAL_DOWN_NOT_SUBMITTED:WR_PHYSICAL_DOWN_UNCERTAIN;}
int main(void){
 struct wr_iot_rc_initial_stop s={0};unsigned char nonce[16]={1};struct wr_iot_physical_initial_request released;
 assert(!wr_iot_rc_initial_stop_begin(&s,nonce));wr_iot_rc_shutdown.active=1;
 assert(wr_iot_rc_initial_stop_begin(&s,nonce));assert(!wr_iot_rc_initial_stop_begin(&s,nonce));
 s.owner++;assert(!wr_iot_rc_initial_stop_step(&s)&&!aux);s.owner--;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_rc_initial_stop_step(&s)&&!aux);wr_iot_rc_shutdown.pending=0;
 for(unsigned i=0;i<7;i++)assert(!wr_iot_rc_initial_stop_step(&s));
 assert(aux==6&&!calls&&!downs);fail_observe=1;assert(!wr_iot_rc_initial_stop_step(&s)&&!calls);fail_observe=0;
 assert(!wr_iot_rc_initial_stop_step(&s));uncertain=1;assert(!wr_iot_rc_initial_stop_step(&s)&&calls==1&&!downs);
 uncertain=0;assert(!wr_iot_rc_initial_stop_step(&s));assert(!wr_iot_rc_initial_stop_step(&s)&&downs==1);
 assert(!wr_iot_rc_initial_stop_released(&s,&released)&&!released.action);
 for(unsigned i=0;i<3;i++)assert(!wr_iot_rc_initial_stop_step(&s)&&downs==1);
 status=WR_STOP_COMPLETE;assert(!wr_iot_rc_initial_stop_step(&s));assert(wr_iot_rc_initial_stop_step(&s)==1);
 assert(wr_iot_rc_initial_stop_released(&s,&released)&&released.action==WR_STOP_RELEASE&&released.attempt==7);
 int before=calls;assert(wr_iot_rc_initial_stop_step(&s)==1&&calls==before&&downs==1&&!depth);
 s=(struct wr_iot_rc_initial_stop){0};aux=calls=downs=0;no_submit=1;
 assert(wr_iot_rc_initial_stop_begin(&s,nonce));
 for(unsigned i=0;i<10;i++)assert(!wr_iot_rc_initial_stop_step(&s));
 assert(downs==1&&s.session.phase==WR_INITIAL_PHYSICAL_SESSION_CANCEL);
 uncertain=1;assert(!wr_iot_rc_initial_stop_step(&s)&&downs==1);
 uncertain=0;assert(wr_iot_rc_initial_stop_step(&s)==-1);
 before=calls;assert(wr_iot_rc_initial_stop_step(&s)==-1&&calls==before);
 assert(!wr_iot_rc_initial_stop_released(&s,&released)&&!released.action&&!depth);
 return 0;
}
