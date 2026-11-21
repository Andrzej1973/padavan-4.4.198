#define main close_enter_regression
#include "check-driver-api-close-enter.c"
#undef main
static int scheduled_calls,schedule_accept,poll_calls,poll_status;
static int wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad){assert(ad&&!locked);poll_calls++;return poll_status;}
static int work_busy(struct close_test_work *w){assert(locked);return w->busy;}
static int schedule_work(struct close_test_work *w){assert(locked);scheduled_calls++;if(schedule_accept)w->busy=1;return schedule_accept;}
#include "driver-api-close-recovery-binding.inc"
#include "driver-api-close-synchronous-put.h"
static int rtnl_is_locked(void){return 1;}
#include "driver-api-close-synchronous-put.inc"
#include "driver-api-close-finish-recovery.inc"
int main(void){
 close_enter_regression();
 for(unsigned fault=0;fault<8;fault++){
  RTMP_ADAPTER ad={0};int dev,main_dev;scheduled_calls=poll_calls=poll_status=0;schedule_accept=1;
  ad.chip=1;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;ad.net_dev=&main_dev;
  struct wr_iot_driver_close_owner *c=&ad.wr_iot_close_owner;
  struct wr_iot_interface_ref *r=&ad.wr_iot_interface_refs[1];
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  assert(wr_iot_radio_begin_stop(&ad.wr_iot_transition,2,&c->ticket));
  c->active=c->consumed=c->uncertain=c->netdev_held=c->module_held=1;
  c->device=&dev;c->generation=2;c->open_token=3;
  r->device=&dev;r->generation=2;r->last_token=3;r->published=1;r->family=WR_REF_FAMILY_MBSS;
  r->phase=WR_REF_CLOSING;r->close_stage=2;r->close_serial=c->ticket.serial;
  r->close_epoch=c->ticket.epoch;r->close_vendor_count=2;
  r->close_prior_phase=(int)c->ticket.prior_phase;r->close_prior_ready=c->ticket.prior_ready;
  switch(fault){case 1:schedule_accept=0;break;case 2:ad.wr_iot_mbss_work[1].work.busy=1;break;
   case 3:ad.wr_iot_mbss_reaper_gate.stopped=1;break;case 4:r->generation++;break;
   case 5:ad.wr_iot_transition.retiring=1;break;case 6:break;case 7:poll_status=-1;break;}
  struct wr_iot_driver_close_owner before=*c;
  struct wr_iot_mbss_recovery_owner recovery_before=ad.wr_iot_mbss_recovery[1];
  c->task=current;c->uncertain=0;
  before=*c;
  int result=-1;
  assert(!wr_iot_driver_close_finish_recover(&ad,&dev,fault==6?&foreign:current,0,&result));
  assert(result==(fault==0?0:(fault==1||fault==7)?1:-1));
  assert(!locked&&!ad.wr_iot_mbss_reaper_gate.submissions);
  assert(scheduled_calls==(fault<2||fault==7));
  assert(poll_calls==(fault<2||fault==7));
  if(fault<2||fault==7){
   assert(!c->netdev_held&&c->module_held&&c->active&&c->recovery_netdev_transferred);
   assert(ad.wr_iot_mbss_recovery[1].phase==(fault==1?WR_MBSS_OWNER_RETAINED:WR_MBSS_OWNER_QUEUED));
   assert(wr_iot_driver_close_recovery_submit(&ad,&dev)==-1);
   assert(scheduled_calls==1);
   int again=99;assert(!wr_iot_driver_close_finish_recover(&ad,&dev,current,0,&again));
   assert(again==-1&&scheduled_calls==1&&poll_calls==1);
  }else{
   if(fault==6)assert(!memcmp(&before,c,sizeof(before)));
   else assert(c->active&&c->uncertain&&!c->task&&c->netdev_held&&c->module_held);
   assert(!memcmp(&recovery_before,&ad.wr_iot_mbss_recovery[1],sizeof(recovery_before)));
  }
 }
 puts("PASS staged scheduling: once-only transfer, success queues, schedule refusal retains, work/reaper/identity/retirement conflicts refuse without transfer");
 return 0;
}
