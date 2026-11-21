#include <assert.h>
#include <stdio.h>
#include <stddef.h>
#include "physical-stop-lifetime.h"
struct task_struct {unsigned refs;};
struct net_device {unsigned refs;};
static struct task_struct owner={1},foreign={1};
static struct task_struct *current=&owner;
static int module_refs=1,fail_module,locked;
static struct wr_iot_physical_stop_pins *dropping;
static struct wr_iot_physical_stop_lifetime *return_lifetime;
#define THIS_MODULE ((void*)1)
static int try_module_get(void*m){assert(m==THIS_MODULE&&!locked);if(fail_module)return 0;module_refs++;return 1;}
static void module_put(void*m){assert(m==THIS_MODULE&&!locked&&module_refs>1);if(return_lifetime)assert(wr_iot_physical_stop_lifetime_blocks(return_lifetime));module_refs--;}
static void get_task_struct(struct task_struct*t){assert(!locked&&t->refs);t->refs++;}
static void put_task_struct(struct task_struct*t){assert(!locked&&t->refs>1);t->refs--;}
static void dev_hold(struct net_device*d){assert(!locked&&d->refs);d->refs++;}
static void dev_put(struct net_device*d);
#include "physical-stop-record.h"
#include "physical-stop-pins.inc"
static void dev_put(struct net_device*d){assert(!locked&&d->refs>1);assert(dropping&&!dropping->module&&!dropping->device&&!dropping->task);assert(!wr_iot_physical_stop_pins_drop(dropping));d->refs--;}
int main(void){
 struct net_device dev={1};struct wr_iot_physical_stop_pins pins={0};
 assert(!wr_iot_physical_stop_pins_acquire(&pins,&foreign,&dev));
 fail_module=1;assert(!wr_iot_physical_stop_pins_acquire(&pins,current,&dev));
 assert(module_refs==1&&owner.refs==1&&dev.refs==1&&!pins.module);
 fail_module=0;assert(wr_iot_physical_stop_pins_acquire(&pins,current,&dev));
 assert(module_refs==2&&owner.refs==2&&dev.refs==2);
 assert(!wr_iot_physical_stop_pins_acquire(&pins,current,&dev));
 dropping=&pins;assert(wr_iot_physical_stop_pins_drop(&pins));
 assert(module_refs==1&&owner.refs==1&&dev.refs==1);
 assert(!wr_iot_physical_stop_pins_drop(&pins));
 struct wr_iot_physical_stop_pins slot={0},detached={0};
 struct wr_iot_physical_stop_record record={0};
 struct wr_iot_peer_close_executor executor={0};unsigned char nonce[16]={1};
 assert(!wr_iot_physical_stop_blocks_retirement(&record,&slot));
 assert(wr_iot_physical_stop_blocks_retirement(NULL,&slot));
 assert(wr_iot_physical_stop_blocks_retirement(&record,NULL));
 for(unsigned bits=1;bits<32;bits++){
  struct wr_iot_physical_stop_record partial={0};
  struct wr_iot_physical_stop_pins partial_pins={0};
  if(bits&1)partial.phase=WR_PHYS_STOP_ARMED;
  if(bits&2)partial.task=current;
  if(bits&4)partial_pins.module=1;
  if(bits&8)partial_pins.task=current;
  if(bits&16)partial_pins.device=&dev;
  assert(wr_iot_physical_stop_blocks_retirement(&partial,&partial_pins));
 }

 struct wr_iot_physical_stop_lifetime lifetime={0};
 struct wr_iot_radio_transition radio;wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 assert(wr_iot_physical_stop_lifetime_begin(&lifetime,&radio)==1);
 return_lifetime=&lifetime;
 assert(wr_iot_physical_stop_pins_acquire(&pins,current,&dev));
 locked=1;
 assert(wr_iot_physical_stop_pins_publish(&slot,&pins,&record,1,2,3,4,nonce,&executor));
 assert(!pins.module&&slot.module&&record.task==current);
 assert(wr_iot_physical_stop_blocks_retirement(&record,&slot));
 assert(!wr_iot_physical_stop_pins_detach(&slot,&detached,&record,1,1,2,nonce,0));
 assert(wr_iot_physical_stop_pins_detach(&slot,&detached,&record,1,1,2,nonce,1));
 assert(!slot.module&&detached.module&&record.phase==WR_PHYS_STOP_IDLE);
 /* RTNL must remain held until detached reference return, as documented. */
 assert(!wr_iot_physical_stop_pins_detach(&slot,&pins,&record,1,1,2,nonce,1));
 assert(!wr_iot_physical_stop_lifetime_end(&lifetime,1,1,0));
 assert(wr_iot_physical_stop_lifetime_blocks(&lifetime));
 locked=0;dropping=&detached;assert(wr_iot_physical_stop_pins_drop(&detached));
 assert(wr_iot_physical_stop_lifetime_blocks(&lifetime));
 locked=1;assert(wr_iot_physical_stop_lifetime_end(&lifetime,1,record.phase==WR_PHYS_STOP_IDLE,!detached.module&&!detached.task&&!detached.device));locked=0;
 assert(!wr_iot_physical_stop_lifetime_blocks(&lifetime));return_lifetime=NULL;
 assert(module_refs==1&&owner.refs==1&&dev.refs==1);
 assert(wr_iot_physical_stop_pins_acquire(&pins,current,&dev));
 locked=1;
 assert(!wr_iot_physical_stop_pins_publish(&slot,&pins,&record,1,2,3,4,nonce,&executor));
 assert(pins.module&&!slot.module&&record.serial==1); /* replay refuses without transfer */
 nonce[0]=2;
 assert(wr_iot_physical_stop_pins_publish(&slot,&pins,&record,1,2,3,4,nonce,&executor));
 assert(wr_iot_physical_stop_begin(&record,2,1,2,nonce,current));
 assert(!wr_iot_physical_stop_pins_detach(&slot,&detached,&record,2,1,2,nonce,1));
 struct wr_iot_peer_table_owner table={.closed=1};
 assert(wr_iot_physical_stop_finish(&record,2,1,2,nonce,current,1,&executor,&table,2));
 assert(wr_iot_physical_stop_pins_detach(&slot,&detached,&record,2,1,2,nonce,0));
 locked=0;dropping=&detached;assert(wr_iot_physical_stop_pins_drop(&detached));
 assert(module_refs==1&&owner.refs==1&&dev.refs==1);
 assert(wr_iot_physical_stop_pins_acquire(&pins,current,&dev));nonce[0]=3;locked=1;
 assert(wr_iot_physical_stop_pins_publish(&slot,&pins,&record,1,2,3,4,nonce,&executor));
 assert(wr_iot_physical_stop_begin(&record,3,1,2,nonce,current));
 assert(!wr_iot_physical_stop_finish(&record,3,1,2,nonce,current,0,&executor,&table,2));
 assert(!wr_iot_physical_stop_pins_detach(&slot,&detached,&record,3,1,2,nonce,0));
 assert(!wr_iot_physical_stop_pins_detach(&slot,&detached,&record,3,1,2,nonce,1));
 assert(slot.module&&slot.task==current&&record.phase==WR_PHYS_STOP_FAILED);
 assert(wr_iot_physical_stop_blocks_retirement(&record,&slot));
 locked=0;assert(module_refs==2&&owner.refs==2&&dev.refs==2);
 /* Failure retains ownership by design; no force-release in this fixture. */
 puts("PASS actual extra kernel pin bundle: exact current task, module refusal no leak, acquire once/drop once, clear before dev_put reentry, no native references consumed; removal/admission unbound");
}
