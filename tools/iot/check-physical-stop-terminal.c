#include <assert.h>
#include <stdio.h>
#include <string.h>
struct pid {unsigned refs;};
static struct pid owner={1},foreign={1};
static struct pid *current=&owner;
static struct pid *task_pid(struct pid*p){return p;}
static struct pid *get_pid(struct pid*p){assert(p&&p->refs);p->refs++;return p;}
static void put_pid(struct pid*p){assert(p&&p->refs>1);p->refs--;}
#include "physical-stop-terminal.inc"
int main(void){
 unsigned char wire[64];
 for(unsigned action=WR_STOP_CANCEL;action<=WR_STOP_RELEASE;action++){
  struct wr_iot_physical_stop_terminal cache={0};
  struct wr_iot_physical_stop_request r={.action=action,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}};
  cache.origin.valid=1;cache.origin.main_generation=99;
  assert(wr_iot_physical_stop_terminal_prepare(&cache,&r)&&owner.refs==2);
  assert(!cache.origin.valid&&!cache.origin.main_generation);
  assert(!wr_iot_physical_stop_terminal_prepare(&cache,&r)&&owner.refs==2);
  assert(!wr_iot_physical_stop_terminal_reply(&cache,&r,wire,64));
  for(unsigned missing=0;missing<3;missing++)assert(!wr_iot_physical_stop_terminal_commit(&cache,missing!=0,missing!=1,missing!=2));
  current=&foreign;assert(!wr_iot_physical_stop_terminal_commit(&cache,1,1,1));current=&owner;
  assert(wr_iot_physical_stop_terminal_commit(&cache,1,1,1));
  assert(!wr_iot_physical_stop_terminal_commit(&cache,1,1,1));
  for(unsigned retry=0;retry<3;retry++){
   struct wr_iot_physical_stop_terminal before=cache;
   assert(wr_iot_physical_stop_terminal_reply(&cache,&r,wire,64));
   struct wr_iot_physical_stop_response response;
   assert(wr_iot_physical_stop_response_decode(&response,wire,64,&r));
   assert(response.status==(action==WR_STOP_CANCEL?WR_STOP_CANCELLED:WR_STOP_RELEASED));
   assert(!memcmp(&before,&cache,sizeof(cache))&&owner.refs==2);
  }
  current=&foreign;assert(!wr_iot_physical_stop_terminal_reply(&cache,&r,wire,64));current=&owner;
  r.attempt++;assert(!wr_iot_physical_stop_terminal_reply(&cache,&r,wire,64));r.attempt--;
  r.nonce[0]++;assert(!wr_iot_physical_stop_terminal_reply(&cache,&r,wire,64));r.nonce[0]--;
  assert(wr_iot_physical_stop_terminal_clear(&cache)&&owner.refs==1);
  assert(!wr_iot_physical_stop_terminal_clear(&cache)&&owner.refs==1);
  assert(!wr_iot_physical_stop_terminal_reply(&cache,&r,wire,64));
 }
 puts("PASS bounded terminal cache: PID reference identity, incomplete cleanup refuses publish, repeat response read-only/no extra holds, foreign/stale refusal, clear once; real cleanup/dispatch binding pending");
}
