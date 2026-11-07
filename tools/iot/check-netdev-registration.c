#include "radio-transition.h"
#include "interface-registry.h"
#include "mbss-retirement.h"
#include <assert.h>
#include <stddef.h>
typedef int INT;typedef unsigned int UINT;typedef unsigned char UCHAR;typedef unsigned long ULONG;
typedef int *PNET_DEV;struct wifi_dev {unsigned int func_idx;};
typedef struct {int value,priv_flags;void *wdev;} RTMP_OS_NETDEV_OP_HOOK;
#define WDEV_NUM_MAX 1
#define INT_MAIN 0
#define INT_MBSSID 2
#define INT_APCLI 3
#define INT_WDS 4
#define INT_MONITOR 5
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
typedef struct {int wr_iot_transition_lock,wr_iot_registration_wait;struct wr_iot_radio_transition wr_iot_transition;struct wr_iot_interface_ref wr_iot_interface_refs[2];struct wr_bss_retirement wr_iot_mbss[WDEV_NUM_MAX];unsigned long wr_iot_registration_generation;unsigned int wr_iot_registration_inflight;} RTMP_ADAPTER;
static int held,result,calls,wakeups,pm_during_attach,snapshot_pins;static RTMP_ADAPTER *current;
static void snapshot_pin(const void *device){assert(device);snapshot_pins++;}
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,assert(!held),held=1,(void)(lock))
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
#define wake_up_all(queue) ((void)(queue),assert(!held),wakeups++)
static int RtmpOSNetDevAttach(UCHAR mode,PNET_DEV dev,RTMP_OS_NETDEV_OP_HOOK *hook){assert(!held&&mode==1&&hook);calls++;int found=0;for(int i=0;i<2;i++)if(current->wr_iot_interface_refs[i].device==dev)found++;assert(found==1&&current->wr_iot_registration_inflight==1);if(pm_during_attach){assert(wr_iot_radio_request_suspend(&current->wr_iot_transition));pm_during_attach=0;}return result;}
#include "netdev-registration.inc"
int main(void){RTMP_ADAPTER a={0};RTMP_OS_NETDEV_OP_HOOK hook={0};int d1=0,d2=0,d3=0;current=&a;wr_iot_radio_transition_init(&a.wr_iot_transition);
result=1;assert(wr_iot_netdev_attach_checked(&a,1,&d1,&hook)==1&&calls==1);assert(!a.wr_iot_interface_refs[0].device&&a.wr_iot_registration_generation==1);
result=0;assert(wr_iot_netdev_attach_checked(&a,1,&d1,&hook)==0&&calls==2&&a.wr_iot_registration_generation==2);
assert(a.wr_iot_interface_refs[0].family==WR_REF_FAMILY_MAIN);
assert(wr_iot_netdev_attach_checked(&a,1,&d1,&hook)==1&&calls==2);
assert(wr_iot_netdev_attach_checked(&a,1,&d2,&hook)==0&&calls==3);
assert(wr_iot_netdev_attach_checked(&a,1,&d3,&hook)==1&&calls==3);
wr_iot_radio_retire(&a.wr_iot_transition);assert(wr_iot_netdev_attach_checked(&a,1,&d3,&hook)==1&&calls==3&&!held);
assert(a.wr_iot_registration_inflight==0&&wakeups==3);
{RTMP_ADAPTER b={0};current=&b;wr_iot_radio_transition_init(&b.wr_iot_transition);
 b.wr_iot_transition.phase=WR_RADIO_READY;b.wr_iot_transition.main_ready=1;
 pm_during_attach=1;assert(wr_iot_netdev_attach_checked(&b,1,&d3,&hook)==0);
 assert(b.wr_iot_interface_refs[0].published&&b.wr_iot_registration_inflight==0&&wakeups==4);
 assert(wr_iot_netdev_attach_checked(&b,1,&d2,&hook)==1&&b.wr_iot_registration_generation==1);
 assert(wr_iot_netdev_mark_removing(&b,&d3)==0);
 assert(wr_iot_netdev_mark_removing(&b,&d3)==1);
 {const void *snapshot[2]={0};
  assert(wr_iot_registry_snapshot(b.wr_iot_interface_refs,2,snapshot,2,
   snapshot_pin)==0&&!snapshot_pins);}
 assert(wr_iot_netdev_cancel_removing_unmutated(&b,&d3)==1);
 assert(b.wr_iot_interface_refs[0].removing);
 assert(wr_iot_radio_abort_suspend(&b.wr_iot_transition));
 assert(wr_iot_netdev_cancel_removing_unmutated(&b,&d3)==0);
 assert(!b.wr_iot_interface_refs[0].removing);
 assert(wr_iot_netdev_mark_removing(&b,&d3)==0);
 assert(wr_iot_registry_kernel_done(&b.wr_iot_interface_refs[0],&d3,
  b.wr_iot_interface_refs[0].generation));
 assert(wr_iot_netdev_cancel_removing_unmutated(&b,&d3)==1);}
{RTMP_ADAPTER c={0};struct wifi_dev wdev={0};
 RTMP_OS_NETDEV_OP_HOOK mbss={0};current=&c;
 wr_iot_radio_transition_init(&c.wr_iot_transition);
 wr_bss_retirement_init(&c.wr_iot_mbss[0]);
 mbss.priv_flags=INT_MBSSID;mbss.wdev=&wdev;
 result=1;
 assert(wr_iot_netdev_attach_checked(&c,1,&d1,&mbss)==1);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_ABSENT);
 result=0;
 assert(wr_iot_netdev_attach_checked(&c,1,&d1,&mbss)==0);
 assert(c.wr_iot_interface_refs[0].family==WR_REF_FAMILY_MBSS);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_LIVE);
 assert(c.wr_iot_mbss[0].generation==c.wr_iot_interface_refs[0].generation);
 assert(wr_iot_netdev_attach_checked(&c,1,&d2,&mbss)==1);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_LIVE);
 c.wr_iot_transition.busy=WR_RADIO_BSS_CLOSE;
 c.wr_iot_interface_refs[0].phase=WR_REF_RESERVED;
 assert(wr_iot_netdev_mark_removing(&c,&d1)==NDIS_STATUS_FAILURE);
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==NDIS_STATUS_FAILURE);
 assert(!c.wr_iot_interface_refs[0].removing&&
        c.wr_iot_mbss[0].stage==WR_BSS_LIVE);
 c.wr_iot_interface_refs[0].phase=WR_REF_OWNED;
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==NDIS_STATUS_FAILURE);
 c.wr_iot_interface_refs[0].phase=WR_REF_IDLE;
 c.wr_iot_transition.active_tx=1;
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==NDIS_STATUS_FAILURE);
 c.wr_iot_transition.active_tx=0;
 c.wr_iot_interface_refs[0].last_token=1;
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==NDIS_STATUS_FAILURE);
 c.wr_iot_interface_refs[0].open_unmutated=1;
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==0);
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==0);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_REMOVING);
 assert(wr_iot_mbss_cancel_unmutated(&c,0,&d1)==0);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_LIVE);
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==0);
 assert(wr_iot_mbss_beacon_done(&c,0,&d1)==0);
 assert(wr_iot_mbss_cancel_unmutated(&c,0,&d1)==NDIS_STATUS_FAILURE);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_BEACON_DONE);}
{RTMP_ADAPTER c={0};struct wifi_dev wdev={0};
 RTMP_OS_NETDEV_OP_HOOK mbss={0};current=&c;
 wr_iot_radio_transition_init(&c.wr_iot_transition);
 wr_bss_retirement_init(&c.wr_iot_mbss[0]);
 mbss.priv_flags=INT_MBSSID;mbss.wdev=&wdev;result=0;
 assert(wr_iot_netdev_attach_checked(&c,1,&d1,&mbss)==0);
 c.wr_iot_transition.busy=WR_RADIO_BSS_CLOSE;
 c.wr_iot_interface_refs[0].last_token=1;
 c.wr_iot_interface_refs[0].close_stage=4;
 assert(wr_iot_mbss_begin_remove(&c,0,&d1)==NDIS_STATUS_SUCCESS);
}
{RTMP_ADAPTER c={0};struct wifi_dev wdev={0};
 RTMP_OS_NETDEV_OP_HOOK mbss={0};current=&c;
 wr_iot_radio_transition_init(&c.wr_iot_transition);
 c.wr_iot_transition.phase=WR_RADIO_READY;c.wr_iot_transition.main_ready=1;
 wr_bss_retirement_init(&c.wr_iot_mbss[0]);
 mbss.priv_flags=INT_MBSSID;mbss.wdev=&wdev;
 result=0;pm_during_attach=1;
 assert(wr_iot_netdev_attach_checked(&c,1,&d1,&mbss)==0);
 assert(c.wr_iot_transition.pm_suspending);
 assert(c.wr_iot_registration_inflight==0);
 assert(c.wr_iot_mbss[0].stage==WR_BSS_LIVE);
 assert(c.wr_iot_mbss[0].generation==c.wr_iot_interface_refs[0].generation);
 assert(wr_iot_netdev_attach_checked(&c,1,&d2,&mbss)==1);}
 {const int flags[]={INT_APCLI,INT_WDS,INT_MONITOR};
  const enum wr_iot_ref_family families[]={WR_REF_FAMILY_APCLI,
   WR_REF_FAMILY_WDS,WR_REF_FAMILY_MONITOR};
  for(unsigned int i=0;i<3;i++){
   RTMP_ADAPTER x={0};RTMP_OS_NETDEV_OP_HOOK aux={0};
   current=&x;result=0;wr_iot_radio_transition_init(&x.wr_iot_transition);
   aux.priv_flags=flags[i];
   assert(wr_iot_netdev_attach_checked(&x,1,&d1,&aux)==0);
   assert(x.wr_iot_interface_refs[0].family==families[i]);
  }
  {RTMP_ADAPTER x={0};RTMP_OS_NETDEV_OP_HOOK unknown={0};int before=calls;
   current=&x;wr_iot_radio_transition_init(&x.wr_iot_transition);
   unknown.priv_flags=99;
   assert(wr_iot_netdev_attach_checked(&x,1,&d1,&unknown)==1);
   assert(calls==before&&x.wr_iot_registration_generation==0);
  }
 }
 return 0;}
