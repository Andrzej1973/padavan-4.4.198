#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include "start-admission.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fault,depth,reads,takes,finishes,stages;
int wr_iot_service_guard_dup(void){assert(depth);return open("/dev/null",O_RDONLY);}
static const char *reader(void *c,const char *k){(void)c;(void)k;return "1";}
int wr_iot_request_stage_from(const char *(*read)(void *,const char *),void *c,int mode,int radio,int band){assert(read&&depth&&mode==1&&radio==1&&!band);stages++;(void)c;return fault!=11;}
int wr_iot_service_guard_enter(int enabled){assert(enabled);if(fault==1)return 0;depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_driver_initial_idle_read(const unsigned char *nonce,struct wr_iot_idle_result *out){
 assert(depth&&nonce&&nonce[0]==1);reads++;*out=(struct wr_iot_idle_result){1,2,(unsigned)reads};
 if(fault==2)return 0;
 if(reads==2){if(fault==4||fault==10)return 0;if(fault==5)out->epoch++;if(fault==6)out->generation++;if(fault==7)out->serial=1;if(fault==8)wr_iot_rc_shutdown.pending=SIGTERM;}
 return 1;
}
int wr_iot_request_snapshot_take(struct wr_iot_request_snapshot *s){takes++;if(fault==3)return 0;s->active=1;s->token=1;s->owner=getpid();depth++;return 1;}
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot *s){assert(s->active&&depth);finishes++;if(fault==9||fault==10)return 0;memset(s,0,sizeof(*s));depth--;return 1;}
#include "start-admission.c"
int main(void){
 unsigned char nonce[16]={1};
 for(fault=0;fault<9;fault++){
  struct wr_iot_start_admission s={0};depth=reads=takes=finishes=0;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_start_admission_begin(&s,nonce)==(fault==0));
  if(!fault){assert(s.admitted&&depth==1&&s.idle.serial==2);assert(!wr_iot_start_admission_begin(&s,nonce));assert(wr_iot_start_admission_cancel(&s)&&!depth);}
  else assert(!depth&&!s.snapshot.active&&!s.admitted);
 }
 struct wr_iot_start_admission s={0};fault=0;depth=reads=0;wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_start_admission_begin(&s,nonce));fault=9;
 assert(!wr_iot_start_admission_cancel(&s)&&s.admitted&&s.snapshot.active&&depth==1);
 fault=0;assert(wr_iot_start_admission_cancel(&s)&&!depth);
 reads=0;fault=10;assert(!wr_iot_start_admission_begin(&s,nonce)&&s.snapshot.active&&depth==1&&!s.admitted);
 fault=0;assert(wr_iot_start_admission_cancel(&s)&&!depth);
 for(int partial=0;partial<2;partial++){
  depth=reads=stages=0;fault=0;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_start_admission_begin(&s,nonce));
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_start_admission_stage(&s,nonce,reader,NULL,1,1,0)&&!stages&&!s.mutation_started);
  wr_iot_rc_shutdown.pending=0;fault=partial?11:0;
  assert(wr_iot_start_admission_stage(&s,nonce,reader,NULL,1,1,0)==!partial);
  assert(stages==1&&s.mutation_started&&s.staged==!partial&&depth==1);
  assert(!wr_iot_start_admission_cancel(&s)&&depth==1&&s.snapshot.active);
  assert(!wr_iot_start_admission_stage(&s,nonce,reader,NULL,1,1,0)&&stages==1);
  /* Test-only owner cleanup: production needs the full rollback executor. */
  fault=0;assert(wr_iot_request_snapshot_finish(&s.snapshot));memset(&s,0,sizeof(s));
 }
 wr_iot_rc_shutdown.active=0;assert(!wr_iot_start_admission_begin(&s,nonce));
 puts("PASS startup admission and one-shot staging ownership: partial writer retains baseline, cancel/replay refused; shutdown/guard/idle/snapshot refusal, epoch/generation/serial drift, pending shutdown and retained failed capture release; external hooks injected");return 0;
}
