#include <assert.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-wire.h"
typedef int INT;
typedef struct {int mt7603;} RTMP_ADAPTER;
typedef struct {int running;} device,*PNET_DEV;
struct ifreq {void *ifr_data;};
struct namespace {void *user_ns;};
static struct namespace space;
static int task,locked=1,capable=1,copy_error,enter_error,leave_ok=1,open_error;
static unsigned copies,enters,leaves,opens;
#define current (&task)
#define CAP_NET_ADMIN 12
#define IS_MT7603(ad) ((ad)->mt7603)
static int rtnl_is_locked(void){return locked;}
static struct namespace *dev_net(PNET_DEV dev){assert(dev);return &space;}
static int ns_capable(void *ns,int cap){assert(ns==space.user_ns&&cap==12);return capable;}
static int netif_running(PNET_DEV dev){return dev->running;}
static unsigned long copy_from_user(void *to,const void *from,unsigned long n){
 copies++;assert(n==144);if(copy_error)return 1;memcpy(to,from,n);return 0;
}
static int wr_iot_driver_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_open_request *r,void *owner){
 assert(ad&&dev&&owner==current&&r->adapter_epoch==1&&r->device_generation==2);
 assert(!strcmp((const char *)r->password,"password"));enters++;return enter_error;
}
static int wr_iot_driver_request_leave(RTMP_ADAPTER *ad,PNET_DEV dev,void *owner){
 assert(ad&&dev&&owner==current&&enters);leaves++;return leave_ok;
}
static int dev_open(PNET_DEV dev){assert(dev&&enters);opens++;return open_error;}
#include "driver-api-open-entry.inc"
int main(void){
 unsigned char wire[144]={'W','R','I','1',1};
 RTMP_ADAPTER ad={1};device dev={0};struct ifreq rq={wire};
 wire[15]=1;wire[23]=2;wire[24]=3;wire[40]=3;wire[41]=8;
 memcpy(wire+48,"IoT",3);memcpy(wire+80,"password",8);
 assert(wr_iot_driver_open_ioctl(NULL,&dev,&rq)==-EINVAL&&!copies);
 locked=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!copies);locked=1;
 capable=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EPERM&&!copies);capable=1;
 ad.mt7603=0;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EOPNOTSUPP&&!copies);ad.mt7603=1;
 dev.running=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&!copies);dev.running=0;
 copy_error=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EFAULT&&!enters);copy_error=0;
 wire[5]=1;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EINVAL&&!enters);wire[5]=0;
 enter_error=-ESTALE;assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-ESTALE&&!opens&&!leaves);
 enter_error=0;open_error=-EBUSY;
 assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EBUSY&&opens==1&&leaves==1);
 open_error=0;leave_ok=0;
 assert(wr_iot_driver_open_ioctl(&ad,&dev,&rq)==-EUCLEAN&&opens==2&&leaves==2);
 leave_ok=1;assert(!wr_iot_driver_open_ioctl(&ad,&dev,&rq)&&opens==3&&leaves==3);
 puts("PASS actual uninstalled OPEN entry: privilege before copy, syntax/owner refusal, exact open error and mandatory leave; injected owner/dev_open, no real ioctl or RF proof");
 return 0;
}
