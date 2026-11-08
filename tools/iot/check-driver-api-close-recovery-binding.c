#define main close_enter_regression
#include "check-driver-api-close-enter.c"
#undef main
static int scheduled_calls,schedule_accept;
static int work_busy(struct close_test_work *w){assert(locked);return w->busy;}
static int schedule_work(struct close_test_work *w){assert(locked);scheduled_calls++;if(schedule_accept)w->busy=1;return schedule_accept;}
#include "driver-api-close-recovery-binding.inc"
int main(void){
 close_enter_regression();
 for(unsigned fault=0;fault<6;fault++){
  RTMP_ADAPTER ad={0};int dev,main_dev;scheduled_calls=0;schedule_accept=1;
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
   case 5:ad.wr_iot_transition.retiring=1;break;}
  struct wr_iot_driver_close_owner before=*c;
  struct wr_iot_mbss_recovery_owner recovery_before=ad.wr_iot_mbss_recovery[1];
  int result=wr_iot_driver_close_recovery_submit(&ad,&dev);
  assert(result==(fault==0?0:fault==1?1:-1));
  assert(!locked&&!ad.wr_iot_mbss_reaper_gate.submissions);
  assert(scheduled_calls==(fault<2));
  if(fault<2){
   assert(!c->netdev_held&&c->module_held&&c->active&&c->recovery_netdev_transferred);
   assert(ad.wr_iot_mbss_recovery[1].phase==(fault?WR_MBSS_OWNER_RETAINED:WR_MBSS_OWNER_QUEUED));
   assert(wr_iot_driver_close_recovery_submit(&ad,&dev)==-1);
   assert(scheduled_calls==1);
  }else{
   assert(!memcmp(&before,c,sizeof(before)));
   assert(!memcmp(&recovery_before,&ad.wr_iot_mbss_recovery[1],sizeof(recovery_before)));
  }
 }
 puts("PASS staged scheduling: once-only transfer, success queues, schedule refusal retains, work/reaper/identity/retirement conflicts refuse without transfer");
 return 0;
}
