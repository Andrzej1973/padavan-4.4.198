#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-retirement.h"
#ifdef WR_CLOSE_KERNEL_BINDING_TEST
#define INT int
#define WDEV_NUM_MAX 1
struct work_struct {int busy;};
typedef struct {
 int chip;unsigned count;
 void *net_dev;
 struct {unsigned BssidNum;struct {struct {const void *if_dev;}wdev;}MBSSID[3];}ApCfg;
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct wr_iot_mbss_poll_lifetime wr_iot_mbss_poll_state;
 struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;
 struct {unsigned deferred_owners;}wr_iot_main_recovery;
 struct work_struct wr_iot_main_recovery_work;
 struct {struct work_struct work;}wr_iot_main_recovery_reap_work,wr_iot_mbss_poll_work,wr_iot_mbss_work[2];
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->chip)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
static int test_locked;
static int work_busy(struct work_struct *w){assert(test_locked);return w->busy;}
#include "driver-api-close-retirement-binding.inc"
#endif
int main(void){
 #ifdef WR_CLOSE_KERNEL_BINDING_TEST
 const unsigned cases=20;
#else
 const unsigned cases=17;
#endif
 for(unsigned fault=0;fault<cases;fault++){
  struct wr_iot_driver_close_owner close={0};struct wr_iot_radio_transition radio;
  struct wr_iot_interface_ref refs[2]={{0}};struct wr_iot_mbss_recovery_owner owners[2];
  struct wr_iot_mbss_poll_lifetime poll;struct wr_iot_mbss_reaper_gate reaper;
  int main_dev,dev,idle=1;unsigned long seq=0;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  wr_iot_mbss_poll_init(&poll);wr_iot_mbss_reaper_gate_init(&reaper);
  for(unsigned i=0;i<2;i++)wr_iot_mbss_recovery_init(&owners[i]);
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(refs,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(refs,2,&seq,&dev,WR_REF_FAMILY_MBSS);
  main->published=r->published=1;main->phase=WR_REF_OWNED;main->last_token=1;r->last_token=2;
  close.active=close.consumed=close.module_held=close.recovery_netdev_transferred=close.recovery_netdev_returned=1;
  close.device=&dev;close.generation=2;close.open_token=2;close.ticket.epoch=radio.epoch;
  close.ticket.serial=3;close.ticket.operation=WR_RADIO_BSS_CLOSE;
  r->phase=WR_REF_IDLE;r->close_stage=4;r->close_serial=3;r->close_epoch=radio.epoch;r->close_vendor_count=2;
  switch(fault){case 1:poll.unjoined=1;break;case 2:poll.pending=1;break;case 3:poll.running=1;break;
   case 4:poll.joining=1;break;case 5:reaper.reaping=1;break;case 6:owners[1].deferred_owners=1;break;
   case 7:idle=0;break;case 8:close.recovery_netdev_returned=0;break;case 9:close.recovery_join_pending=1;break;
   case 10:r->generation++;break;case 11:main->close_running=1;break;case 12:radio.retiring=1;break;
   case 13:close.module_held=0;break;case 14:close.netdev_held=1;break;case 15:close.ticket.epoch++;break;
   case 16:r->close_prior_ready++;break;
   case 17:idle=2;break;case 18:idle=3;break;case 19:idle=4;break;}
  struct wr_iot_driver_close_owner before=close;
#ifdef WR_CLOSE_KERNEL_BINDING_TEST
  RTMP_ADAPTER ad={0};ad.chip=1;ad.count=1;ad.net_dev=&main_dev;
  ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=close.device;
  ad.wr_iot_close_owner=close;ad.wr_iot_transition=radio;
  memcpy(ad.wr_iot_interface_refs,refs,sizeof(refs));memcpy(ad.wr_iot_mbss_recovery,owners,sizeof(owners));
  ad.wr_iot_mbss_poll_state=poll;ad.wr_iot_mbss_reaper_gate=reaper;
  if(idle==0)ad.wr_iot_mbss_work[1].work.busy=1;
  if(idle==2)ad.wr_iot_main_recovery_work.busy=1;
  if(idle==3)ad.wr_iot_main_recovery_reap_work.work.busy=1;
  if(idle==4)ad.wr_iot_mbss_poll_work.work.busy=1;
  test_locked=1;assert(wr_iot_driver_close_retirement_ready_locked(&ad)==(fault==0));test_locked=0;
  assert(!memcmp(&before,&ad.wr_iot_close_owner,sizeof(before)));
#else
  assert(wr_iot_driver_close_retirement_ready(&close,&radio,refs,2,&main_dev,1,owners,2,&poll,&reaper,idle)==(fault==0));
#endif
  assert(!memcmp(&before,&close,sizeof(close)));
 }
 puts("PASS retirement preflight: exact returned receipt, durable close/Main and joined poll/recovery/work;conflicts refuse without ownership mutation; thread/release unbound");
 return 0;
}
