#include <assert.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-owner.h"
typedef int INT;
typedef struct device {int running;} device,*PNET_DEV;
#define WDEV_NUM_MAX 2
#define VIRTUAL_IF_NUM(ad) ((ad)->vendor_count)
typedef unsigned long ULONG;
typedef struct {
 int mt7603,wr_iot_transition_lock,wr_iot_ticket_wait;
 PNET_DEV net_dev;
 unsigned vendor_count,wr_iot_control_users,wr_iot_control_poisoned;
 unsigned wr_iot_boot_active,wr_iot_boot_failed;
 struct {unsigned BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;
 struct wr_iot_driver_owner wr_iot_driver_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
} RTMP_ADAPTER;
#define RTMP_IRQ_LOCK(lock,flags) do{(flags)=0;assert(!*(lock));*(lock)=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(flags);assert(*(lock));*(lock)=0;}while(0)
#define wake_up_all(queue) (++*(queue))
struct ifreq {void *ifr_data;};
struct namespace {void *user_ns;};
static struct namespace space;
static int current_task_identity,locked=1,capable=1,copy_error,leave_ok=1,open_error,skip_ndo;
static unsigned copies,opens;
static RTMP_ADAPTER *opening;
#define current (&current_task_identity)
#define CAP_NET_ADMIN 12
#define IS_MT7603(ad) ((ad)->mt7603)
static int rtnl_is_locked(void){return locked;}
static struct namespace *dev_net(PNET_DEV dev){assert(dev);return &space;}
static int ns_capable(void *ns,int cap){assert(ns==space.user_ns&&cap==12);return capable;}
static int netif_running(PNET_DEV dev){return dev->running;}
static unsigned long copy_from_user(void *to,const void *from,unsigned long n){
 copies++;assert(n==144||n==32);if(copy_error)return 1;memcpy(to,from,n);return 0;
}
#include "driver-api-owner-binding.inc"
static int dev_open(PNET_DEV dev){
 struct wr_iot_driver_owner *o=&opening->wr_iot_driver_owner;
 struct wr_iot_radio_transition *r=&opening->wr_iot_transition;
 assert(dev&&o->active&&!opening->wr_iot_transition_lock);opens++;
 if(skip_ndo)return -ENETDOWN;
 const struct wr_iot_driver_open_request *request=wr_iot_driver_owner_take(o,current,dev,r,opening->wr_iot_interface_refs,WDEV_NUM_MAX+1);
 assert(request&&!strcmp((const char *)request->password,"password"));
 if(leave_ok){
  struct wr_iot_interface_ref *ref=wr_iot_registry_find(opening->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,o->claim.generation);
  assert(wr_iot_ref_open_finish(ref,dev,o->claim.generation,o->claim.serial,0));
  assert(wr_iot_radio_abort_bss_open_unmutated(r,&o->ticket));
 }
 return open_error;
}
#include "driver-api-open-entry.inc"
static unsigned query_copies;static int query_copy_error;
static unsigned long copy_to_user(void *to,const void *from,unsigned long n){
 assert(n==32&&!opening->wr_iot_transition_lock);query_copies++;
 if(query_copy_error)return 1;
 memcpy(to,from,n);return 0;
}
#include "driver-api-identity.inc"

static int identity_call(RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq){
 unsigned char nonce[16]={3};assert(wr_iot_driver_query_encode((unsigned char *)rq->ifr_data,32,nonce));
 return wr_iot_driver_identity_ioctl(ad,dev,rq);
}
int main(void){
 unsigned char wire[144]={'W','R','I','2',1};
 RTMP_ADAPTER ad={.mt7603=1,.vendor_count=1,.ApCfg.BssidNum=3};
 device dev={0},main_dev={0};struct ifreq rq={wire};unsigned long sequence=0;
 ad.net_dev=&main_dev;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;opening=&ad;
 wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
 struct wr_iot_interface_ref *ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,WDEV_NUM_MAX+1,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
 assert(ref);ref->published=1;ref->phase=WR_REF_OWNED;
 ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,WDEV_NUM_MAX+1,&sequence,&dev,WR_REF_FAMILY_MBSS);assert(ref);ref->published=1;
 wire[15]=1;wire[23]=2;wire[24]=3;wire[40]=3;wire[41]=8;
 memcpy(wire+48,"IoT",3);memcpy(wire+80,"password",8);

 unsigned char identity_wire[32];struct ifreq identity_rq={identity_wire};
 struct wr_iot_driver_identity identity;
 capable=0;assert(identity_call(&ad,&dev,&identity_rq)==-EPERM&&!query_copies);capable=1;
 assert(identity_call(&ad,&main_dev,&identity_rq)==-EBUSY&&!query_copies);
 ad.wr_iot_transition.reset_pending=1;
 assert(identity_call(&ad,&dev,&identity_rq)==-EBUSY&&!query_copies);
 ad.wr_iot_transition.reset_pending=0;
 query_copy_error=1;assert(identity_call(&ad,&dev,&identity_rq)==-EFAULT);
 assert(!ad.wr_iot_driver_owner.query_valid);query_copy_error=0;
 memset(identity_wire,0xa5,sizeof(identity_wire));
 assert(!identity_call(&ad,&dev,&identity_rq));
 assert(wr_iot_driver_identity_decode(&identity,identity_wire,sizeof(identity_wire)));
 assert(identity.adapter_epoch==1&&identity.device_generation==2);
 assert(!ad.wr_iot_transition.serial&&!ad.wr_iot_driver_owner.active);
 for(unsigned i=0;i<32;i++)if((i>=5&&i<8)||i>=24)assert(!identity_wire[i]);
 copies=0;
 assert(wr_iot_driver_open_ioctl(NULL,&dev,&rq)==-EINVAL&&!copies);
 locked=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!copies);locked=1;
 capable=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EPERM&&!copies);capable=1;
 ad.mt7603=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EOPNOTSUPP&&!copies);ad.mt7603=1;
 dev.running=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!copies);dev.running=0;
 copy_error=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EFAULT&&!ad.wr_iot_driver_owner.active);copy_error=0;
 wire[5]=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EINVAL&&!ad.wr_iot_driver_owner.active);wire[5]=0;
 wire[23]=3;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!opens);wire[23]=2;
 ad.wr_iot_control_users=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!opens);ad.wr_iot_control_users=0;
 ad.wr_iot_boot_active=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!opens);ad.wr_iot_boot_active=0;
 skip_ndo=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-ENETDOWN&&opens==1);
 assert(ad.wr_iot_ticket_wait==1&&!ad.wr_iot_driver_owner.active&&!ad.wr_iot_transition.busy);skip_ndo=0;
 assert(!identity_call(&ad,&dev,&identity_rq));
 open_error=-EBUSY;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&opens==2&&!ad.wr_iot_driver_owner.active);
 assert(!identity_call(&ad,&dev,&identity_rq));
 open_error=0;assert(!wr_iot_driver_open_ioctl(&ad,&dev,&rq)&&opens==3);
 assert(!identity_call(&ad,&dev,&identity_rq));
 leave_ok=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EUCLEAN&&opens==4);
 assert(ad.wr_iot_control_poisoned&&ad.wr_iot_driver_owner.poisoned&&!ad.wr_iot_driver_owner.request.password[0]);
 assert(identity_call(&ad,&dev,&identity_rq)==-EBUSY);
 assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&opens==4);
 puts("PASS composed actual OPEN entry and adapter owner: privilege, identity/control/bootstrap refusal, single-ticket consume, open error and poisoned leave; dev_open/netdev hooks injected, no real ioctl or RF proof");
 return 0;
}
