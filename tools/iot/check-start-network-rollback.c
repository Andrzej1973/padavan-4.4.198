#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include "start-network-rollback.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fault,operations,bridge,dns,down,detached,restore_calls,finishes;
static unsigned serial;
static struct wr_iot_start_network_rollback *current;
int wr_iot_service_guard_dup(void){return open("/dev/null",O_RDONLY);}
int wr_iot_driver_initial_idle_read(const unsigned char*n,struct wr_iot_idle_result*out){assert(n[0]==1);*out=(struct wr_iot_idle_result){1,2,++serial};return 1;}
int wr_iot_bss_is_down(void){return 1;}
static int allowed(void){operations++;return fault!=(int)current->phase+1;}
int wr_iot_bridge_set_up(int up){assert(!up);if(!allowed())return 0;down=1;return 1;}
int wr_iot_bridge_detach(void){assert(down);if(!allowed())return 0;detached=1;return 1;}
int wr_iot_bridge_remove(void){assert(detached);if(!allowed())return 0;bridge=0;return 1;}
int wr_iot_dns_activation_recovery_state(void){if(fault==4)return -1;return dns;}
int wr_iot_dns_activation_abort(void){assert(!bridge&&down&&dns);dns=0;return 1;}
int wr_iot_request_snapshot_restore(struct wr_iot_request_snapshot*s){assert(!bridge&&!dns&&s->active);restore_calls++;if(!allowed())return 0;s->recovering=s->restored=1;return 1;}
unsigned int if_nametoindex(const char*n){assert(!strcmp(n,"br-iot"));return bridge;}
int wr_iot_request_snapshot_restored_current(struct wr_iot_request_snapshot*s){return s->restored;}
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot*s){assert(s->active&&s->restored&&!bridge&&!dns);finishes++;if(!allowed())return 0;memset(s,0,sizeof(*s));return 1;}
#include "start-network-rollback.c"
int main(void){
 for(int failure=0;failure<=7;failure++){
  struct wr_iot_start_network_rollback r={0};current=&r;
  struct wr_iot_start_network network={.phase=WR_IOT_NET_RECOVERY,.attempted=127};
  struct wr_iot_start_admission owner={0};owner.admitted=owner.mutation_started=owner.snapshot.active=1;owner.snapshot.owner=getpid();owner.snapshot.token=1;owner.idle=(struct wr_iot_idle_result){1,2,1};
  struct wr_iot_open_controller open={0};unsigned char nonce[16]={1};
  fault=0;serial=1;bridge=dns=1;down=detached=operations=restore_calls=finishes=0;wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
  open.phase=WR_IOT_OPEN_RECOVERY;assert(!wr_iot_start_network_rollback_step(&r,&network,&owner,&open,nonce)&&!operations);open.phase=WR_IOT_OPEN_IDLE;
  if(failure){
   while((int)r.phase+1<failure)assert(!wr_iot_start_network_rollback_step(&r,&network,&owner,&open,nonce));
   fault=failure;
   if(failure!=6){enum wr_iot_start_rollback_phase phase=r.phase;assert(!wr_iot_start_network_rollback_step(&r,&network,&owner,&open,nonce)&&r.phase==phase&&owner.snapshot.active);}
   fault=0;
  }
  int completed=0;for(unsigned budget=0;budget<10&&!completed;budget++)completed=wr_iot_start_network_rollback_step(&r,&network,&owner,&open,nonce);
  assert(completed&&r.phase==WR_IOT_ROLL_DONE&&!bridge&&!dns&&!owner.snapshot.active);
  assert(wr_iot_rc_shutdown.pending==SIGTERM);
  int before=operations;assert(wr_iot_start_network_rollback_step(&r,&network,&owner,&open,nonce)&&operations==before);
  r.owner++;assert(!wr_iot_start_network_rollback_step(&r,&network,&owner,&open,nonce));
 }
 puts("PASS pre-OPEN rollback: ordered bridge/DNS/settings restore, failure retry retains baseline, pending shutdown retained, attempted OPEN refused; resource hooks injected");return 0;
}
