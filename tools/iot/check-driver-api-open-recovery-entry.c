#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-open-recovery-wire.h"
#include "driver-api-open-current-wire.h"
typedef int INT;typedef unsigned long ULONG;typedef const void *PNET_DEV;
#define WDEV_NUM_MAX 1
struct ifreq {void *ifr_data;};
typedef struct {
 struct {int BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;
 struct {int active;} wr_iot_close_owner,wr_iot_closed_probe;
 int wr_iot_transition_lock,wr_iot_driver_owner,wr_iot_transition,wr_iot_interface_refs[2];
 int wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 PNET_DEV net_dev;
} RTMP_ADAPTER;
static int locked,copies,observations,accepted=1,copy_error;
#define VIRTUAL_IF_NUM(ad) 2
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);assert(!locked);locked=1;flags=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);assert(locked&&flags);locked=0;}while(0)
static int wr_iot_driver_open_recovery_observe(const int *owner,const unsigned char *nonce,const int *radio,int *slots,unsigned count,PNET_DEV main_dev,PNET_DEV dev,unsigned vendor,unsigned users,int blocked,int probe,struct wr_iot_driver_open_current_result *out){
 assert(locked&&owner&&nonce[0]==1&&radio&&slots&&count==2&&main_dev!=dev&&vendor==2&&!users&&!blocked&&!probe);observations++;
 out->adapter_epoch=1;out->device_generation=2;out->open_token=3;return accepted;
}
static int copy_to_user(void *out,const void *in,unsigned n){assert(!locked&&n==64);copies++;if(copy_error)return 1;memcpy(out,in,n);return 0;}
#include "driver-api-open-recovery-entry.inc"
int main(void){
 RTMP_ADAPTER ad={0};int main_dev,iot_dev;unsigned char nonce[16]={1},wire[64],reply[64];struct ifreq rq={reply};
 ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
 assert(wr_iot_driver_open_recovery_query_encode(wire,64,nonce));
 assert(!wr_iot_driver_open_recovery_reply(&ad,&iot_dev,&rq,wire)&&copies==1&&observations==1&&!locked);
 struct wr_iot_driver_open_recovery_result result;
 assert(wr_iot_driver_open_recovery_decode(&result,nonce,1,2,reply,64)&&result.open_token==3);
 for(int fault=0;fault<4;fault++){
  assert(wr_iot_driver_open_recovery_query_encode(wire,64,nonce));copies=observations=0;
  ad.wr_iot_close_owner.active=fault==0;ad.ApCfg.BssidNum=fault==1?2:3;
  accepted=fault!=2;copy_error=fault==3;
  assert(wr_iot_driver_open_recovery_reply(&ad,&iot_dev,&rq,wire)==(fault==3?-EFAULT:-EAGAIN));
  assert(!locked&&copies==(fault==3)&&observations==(fault>=2));
 }
 wire[4]=10;assert(wr_iot_driver_open_recovery_reply(&ad,&iot_dev,&rq,wire)==-EINVAL&&!locked);
 puts("PASS actual recovery-only OPEN reply: typed query, third BSS/owner guards, locked observer, unlocked user copy and refusal/error propagation; common RTNL/capability dispatch tested separately");
}
