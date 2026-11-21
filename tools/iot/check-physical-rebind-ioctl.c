#include <assert.h>
#include <errno.h>
#include <string.h>
#include "physical-rebind-wire.h"
typedef int INT;
typedef struct device {int id;} *PNET_DEV;
typedef struct {int mt7603;PNET_DEV net_dev;struct {unsigned BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;} RTMP_ADAPTER;
struct ifreq {void *ifr_data;};struct namespace {void *user_ns;};
static struct namespace space;
static int locked=1,capable=1,copy_fault,race,actor_status,copies,observes,opens;
#define CAP_NET_ADMIN 12
#define IS_MT7603(ad) ((ad)->mt7603)
static int rtnl_is_locked(void){return locked;}
static struct namespace *dev_net(PNET_DEV dev){assert(dev);return &space;}
static int ns_capable(void *ns,int cap){assert(ns==space.user_ns&&cap==12);return capable;}
static unsigned long copy_from_user(void *to,const void *from,unsigned long n){
 copies++;if(copy_fault==copies)return 1;
 memcpy(to,from,n);if(race&&copies==2)((unsigned char *)to)[5]^=3;return 0;
}
static int wr_iot_physical_rebind_observe(RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_physical_stop_request *r)
{assert(ad&&dev&&r->action==WR_STOP_RELEASE);observes++;return actor_status;}
static int wr_iot_physical_rebind_open_execute(RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_physical_stop_request *r,const struct wr_iot_driver_open_request *o)
{assert(ad&&dev&&r->action==WR_STOP_RELEASE&&!strcmp((char *)o->password,"password"));opens++;return actor_status;}
#include "physical-rebind-ioctl.inc"
int main(void){
 struct device main_dev,iot_dev,other;RTMP_ADAPTER ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
 struct wr_iot_physical_rebind_request r={.operation=WR_REBIND_OPEN};
 unsigned char wire[216];struct ifreq rq={wire};
 ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
 r.physical=(struct wr_iot_physical_stop_request){.action=WR_STOP_RELEASE,.epoch=5,.generation=2,.open_token=3,.closed_serial=4,.attempt=6,.nonce={1}};
 r.open=(struct wr_iot_driver_open_request){.adapter_epoch=7,.device_generation=2,.request_id={8},.ssid_length=3,.password_length=8,.ssid="IoT",.password="password"};
 assert(wr_iot_physical_rebind_encode(wire,216,&r));
 locked=0;assert(wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)==-EBUSY&&!copies);locked=1;
 capable=0;assert(wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)==-EPERM&&!copies);capable=1;
 assert(wr_iot_physical_rebind_ioctl(&ad,&other,&rq)==-EOPNOTSUPP&&!copies);
 assert(wr_iot_physical_rebind_ioctl(&ad,&main_dev,&rq)==-EOPNOTSUPP&&!copies);
 for(copy_fault=1;copy_fault<=2;copy_fault++){copies=0;assert(wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)==-EFAULT&&!opens);}
 copy_fault=0;copies=0;race=1;assert(wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)==-EINVAL&&!opens);race=0;
 copies=0;actor_status=-EUCLEAN;assert(wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)==-EUCLEAN&&opens==1&&copies==2);
 r.operation=WR_REBIND_OBSERVE;assert(wr_iot_physical_rebind_encode(wire,72,&r));copies=0;actor_status=0;
 assert(!wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)&&observes==1&&copies==2);
 wire[7]=1;copies=0;assert(wr_iot_physical_rebind_ioctl(&ad,&iot_dev,&rq)==-EINVAL&&copies==1&&observes==1);
 return 0;
}
