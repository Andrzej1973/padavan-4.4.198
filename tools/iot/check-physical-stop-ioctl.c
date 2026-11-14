#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#define INT int
#define ULONG unsigned long
#define CAP_NET_ADMIN 12
struct net {void *user_ns;};
struct device {struct net net;};typedef struct device *PNET_DEV;
struct ifreq {void *ifr_data;};
typedef struct {struct device *net_dev;int wr_iot_transition_lock;struct {unsigned BssidNum;struct {struct {void *if_dev;} wdev;} MBSSID[3];} ApCfg;} RTMP_ADAPTER;
static int held,rtnl=1,permission=1,chip=1,read_fail,write_fail,handler_error,bad_reply,handles,reads,writes;
static int rtnl_is_locked(void){return rtnl;}
static struct net *dev_net(PNET_DEV d){return &d->net;}
static int ns_capable(void *ns,int cap){(void)ns;assert(cap==CAP_NET_ADMIN&&!held);return permission;}
#define IS_MT7603(ad) ((void)(ad),chip)
#define RTMP_IRQ_LOCK(l,f) ((void)(l),(f)=0,assert(!held),held=1)
#define RTMP_IRQ_UNLOCK(l,f) ((void)(l),(void)(f),assert(held),held=0)
static int copy_from_user(void *out,const void *in,unsigned n){assert(!held&&n==64);reads++;if(read_fail)return 1;memcpy(out,in,n);return 0;}
static int copy_to_user(void *out,const void *in,unsigned n){assert(!held&&n==64);writes++;if(write_fail)return 1;memcpy(out,in,n);return 0;}
#include "physical-stop-ioctl.inc"
INT wr_iot_physical_stop_handle(RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_physical_stop_request*r,unsigned char*wire,unsigned n){
 assert(ad&&dev==ad->net_dev&&!held&&rtnl);handles++;
 if(handler_error)return handler_error;
 if(bad_reply)return 0;
 unsigned status=r->action==WR_STOP_ARM?WR_STOP_ARMED:r->action==WR_STOP_CANCEL?WR_STOP_CANCELLED:r->action==WR_STOP_RELEASE?WR_STOP_RELEASED:WR_STOP_COMPLETE;
 assert(wr_iot_physical_stop_response_encode(wire,n,r,r->attempt?r->attempt:1,status));return 0;
}
int main(void){
 struct device main={0},ra2={0};RTMP_ADAPTER ad={.net_dev=&main};ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&ra2;
 unsigned char wire[64];struct ifreq rq={wire};struct wr_iot_physical_stop_request r={.action=WR_STOP_QUERY,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}};
 for(unsigned fault=0;fault<10;fault++){
  rtnl=fault!=1;permission=fault!=2;chip=fault!=3;ad.ApCfg.BssidNum=fault==4?2:3;
  read_fail=fault==5;write_fail=fault==9;handler_error=fault==7?-EBUSY:0;bad_reply=fault==8;
  handles=reads=writes=held=0;assert(wr_iot_physical_stop_request_encode(wire,64,&r));if(fault==6)wire[7]=1;
  int result=wr_iot_physical_stop_ioctl(&ad,&main,&rq);
  assert(!held);assert(result==(fault==0?0:fault==1||fault==4||fault==7?-EBUSY:fault==2?-EPERM:fault==3?-EOPNOTSUPP:fault==5||fault==9?-EFAULT:fault==6?-EINVAL:-EIO));
  assert(handles==(fault==0||fault>=7));assert(writes==(fault==0||fault==9));
 }
 handles=reads=writes=0;rtnl=permission=chip=1;read_fail=write_fail=handler_error=bad_reply=0;
 assert(wr_iot_physical_stop_ioctl(&ad,&ra2,&rq)==-EBUSY&&!handles&&!reads&&!writes);
 puts("PASS actual standalone ioctl wrapper: RTNL/capability/chip/exact main BSS gate, malformed/copy/handler errors, typed output validation, no handler replay on failed copy; transaction handler injected");
}
