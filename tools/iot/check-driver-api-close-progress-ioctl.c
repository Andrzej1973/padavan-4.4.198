#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-progress-wire.h"
typedef int INT;typedef unsigned long ULONG;typedef int *PNET_DEV;
typedef struct {
 int chip,wr_iot_transition_lock;PNET_DEV net_dev;
 struct {unsigned BssidNum;struct {struct {PNET_DEV if_dev;}wdev;}MBSSID[3];}ApCfg;
}RTMP_ADAPTER;
struct ifreq {void *ifr_data;};struct namespace {void *user_ns;};
static struct namespace space;
static int rtnl=1,capable=1,copy_error,locked,copies,progress_calls;
#define CAP_NET_ADMIN 12
#define IS_MT7603(ad) ((ad)->chip)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(locked);locked=0;}while(0)
static int rtnl_is_locked(void){return rtnl;}
static struct namespace *dev_net(PNET_DEV dev){assert(dev);return &space;}
static int ns_capable(void *ns,int cap){assert(ns==space.user_ns&&cap==12);return capable;}
static int copy_from_user(void *to,const void *from,unsigned long n){assert(!locked&&n==64);copies++;if(copy_error)return 1;memcpy(to,from,n);return 0;}
static int wr_iot_driver_close_progress(RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_driver_close_request *r){assert(ad&&dev&&r->open_token==3&&rtnl&&capable&&!locked);progress_calls++;return -EINPROGRESS;}
#include "driver-api-close-progress-entry.inc"
#include "driver-api-close-progress-ioctl.inc"
int main(void){
 for(unsigned fault=0;fault<11;fault++){
  int dev,main_dev,other;RTMP_ADAPTER ad={.chip=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  unsigned char wire[64];struct wr_iot_driver_close_request request={{1},1,2,3};
  assert(wr_iot_driver_close_progress_encode(wire,64,&request));struct ifreq rq={wire};
  rtnl=capable=1;copy_error=locked=copies=progress_calls=0;PNET_DEV target=&dev;
  switch(fault){case 1:rtnl=0;break;case 2:capable=0;break;case 3:ad.chip=0;break;
   case 4:ad.ApCfg.BssidNum=2;break;case 5:ad.ApCfg.BssidNum=4;break;
   case 6:target=&main_dev;break;case 7:target=&other;break;
   case 8:copy_error=1;break;case 9:wire[4]=10;break;case 10:wire[63]=1;break;}
  int result=wr_iot_driver_close_progress_ioctl(&ad,target,&rq);
  int expected=fault==0?-EINPROGRESS:fault==1?-EBUSY:fault==2?-EPERM:fault==3?-EOPNOTSUPP:fault<8?-EBUSY:fault==8?-EFAULT:-EINVAL;
  assert(result==expected&&!locked&&progress_calls==(fault==0));
  assert(copies==(fault==0||fault>=8));
 }
 assert(wr_iot_driver_close_progress_ioctl(NULL,NULL,NULL)==-EINVAL);
 puts("PASS staged progress transport: RTNL/namespace privilege/chip/exact third BSS before copy; fixed64 copy fault/opcode/reserved bytes refuse before orchestration");
}
