#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-wire.h"
typedef int INT;typedef struct {int unused;} RTMP_ADAPTER;
typedef struct {int running;} device,*PNET_DEV;
struct ifreq {void *ifr_data;};static int task;
#define current (&task)
static int enter_status,close_status,finish_ok=1,enters,closes,finishes;
static int netif_running(PNET_DEV dev){return dev->running;}
static int wr_iot_driver_close_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_driver_close_request *r,const void *owner){
 assert(ad&&dev&&owner==current&&r->adapter_epoch==1&&r->device_generation==2&&r->open_token==3&&r->open_request_id[0]==1);enters++;return enter_status;
}
static int dev_close(PNET_DEV dev){assert(enters&&dev);closes++;dev->running=0;return close_status;}
static int wr_iot_driver_close_request_finish(RTMP_ADAPTER *ad,PNET_DEV dev,const void *owner,int status){assert(ad&&dev&&owner==current&&closes&&status==close_status);finishes++;return finish_ok;}
#include "driver-api-close-entry.inc"
int main(void){
 unsigned char wire[64];struct wr_iot_driver_close_request request={{1},1,2,3};
 RTMP_ADAPTER ad={0};device dev={1};struct ifreq rq={wire};
 assert(wr_iot_driver_close_request_encode(wire,64,&request));
 wire[4]=11;assert(wr_iot_driver_close_reply(&ad,&dev,&rq,wire)==-EINVAL&&!enters&&!closes);
 wire[4]=10;dev.running=0;assert(wr_iot_driver_close_reply(&ad,&dev,&rq,wire)==-EAGAIN&&!enters&&!closes);
 dev.running=1;enter_status=-ESTALE;assert(wr_iot_driver_close_reply(&ad,&dev,&rq,wire)==-ESTALE&&!closes&&!finishes);
 enter_status=0;finish_ok=0;assert(wr_iot_driver_close_reply(&ad,&dev,&rq,wire)==-EUCLEAN&&closes==1&&finishes==1&&!dev.running);
 /* Even a nominal dev_close success cannot bypass a refused completion. */
 dev.running=1;finish_ok=1;close_status=-EIO;assert(wr_iot_driver_close_reply(&ad,&dev,&rq,wire)==-EIO&&finishes==2);
 dev.running=1;close_status=0;assert(!wr_iot_driver_close_reply(&ad,&dev,&rq,wire)&&closes==3&&finishes==3);
 puts("PASS proposed CLOSE entry: strict request and current netdev, reserve refusal before close, mandatory checked finish despite admin DOWN, no retry/reopen; strong bindings injected, not installed");
}
