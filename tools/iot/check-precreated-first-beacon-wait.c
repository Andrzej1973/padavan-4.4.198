#define MT7603 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define HIF_MT 1
#define main wr_iot_imported_owner_fixture
#define wr_iot_driver_first_beacon_wait wr_iot_injected_entry_wait
#include "check-driver-api-owner-binding.c"
#undef wr_iot_driver_first_beacon_wait
#undef main
#define WR_IOT_HOST_TEST 1
static int mode,wait_calls;
#define RTMP_SEM_LOCK(p) do{assert(!opening->wr_iot_transition_lock&&!*(p));*(p)=1;}while(0)
#define RTMP_SEM_UNLOCK(p) do{assert(*(p));*(p)=0;}while(0)
#define in_atomic() 0
#define irqs_disabled() 0
#define msecs_to_jiffies(n) (n)
static void wait_step(long budget);
/* Match immediate condition checks, then a spurious recheck before wake. */
#define wait_event_timeout(q,condition,budget) ({ long wr_remaining=(budget); \
 (void)(q); if(condition){assert(condition);} else { \
 assert(!(condition));wait_step(wr_remaining); \
 if(condition){assert(condition);if(wr_remaining>1)wr_remaining--;} \
 else wr_remaining=0; } wr_remaining; })
#include "precreated-first-beacon-wait.inc"
static void wait_step(long budget)
{
 RTMP_ADAPTER *ad=opening;
 struct wr_iot_beacon_producer_ticket pin={0};
 assert(!ad->wr_iot_transition_lock&&!ad->BcnRingLock&&budget>0&&budget<=3000);
 wait_calls++;
 if(!ad->wr_iot_first_beacon.pending){
  assert(wait_calls==1&&budget==3000&&ad->wr_iot_beacon_gates[2].active==1);
  if(mode==11)ad->wr_iot_beacon_gates[2].active=0;
  return;
 }
 assert(wait_calls==(mode==11?2:1)&&budget==(mode==11?2999:3000));
 if(mode==8)return; /* no periodic progress */
 assert(wr_iot_beacon_gate_begin(&ad->wr_iot_beacon_gates[2],7,&pin));
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 wr_iot_first_beacon_capture_locked(ad,2,7);
 if(mode==3)assert(wr_iot_first_beacon_expire(&ad->wr_iot_first_beacon,&ad->wr_iot_first_beacon.identity));
 if(mode==6)ad->wr_iot_first_beacon_capture.device=ad->net_dev;
 if(mode!=1)wr_iot_first_beacon_published_locked(ad,2);
 if(mode==2)ad->wr_iot_transition.main_ready=0;
 if(mode==4)ad->wr_iot_interface_refs[1].generation++;
 if(mode==5)ad->wr_iot_beacon_gates[2].generation++;
 assert(wr_iot_beacon_gate_end(&ad->wr_iot_beacon_gates[2],&pin)||(mode==5));
 if(mode==5)ad->wr_iot_beacon_gates[2].active=0;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
}
int main(void)
{
 for(mode=0;mode<12;mode++){
  RTMP_ADAPTER ad={.mt7603=1,.vendor_count=1,.ApCfg.BssidNum=3};
  device main_dev={1},dev={1};unsigned long seq=0;
  struct wr_iot_driver_open_request request={0};
  struct wr_iot_interface_ref *m,*ref;
  opening=&ad;locked=1;wait_calls=0;ad.chipCap.hif_type=HIF_MT;
  ad.net_dev=&main_dev;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);
  ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&seq,&dev,WR_REF_FAMILY_MBSS);
  assert(m&&ref);m->published=ref->published=1;m->phase=WR_REF_OWNED;
  request.request_id[0]=1;request.adapter_epoch=ad.wr_iot_transition.epoch;request.device_generation=ref->generation;
  assert(wr_iot_driver_owner_query(&ad.wr_iot_driver_owner,request.request_id,request.adapter_epoch,request.device_generation));
  assert(wr_iot_driver_request_enter(&ad,&dev,&request,current)==0);
  assert(wr_iot_driver_owner_take(&ad.wr_iot_driver_owner,current,&dev,&ad.wr_iot_transition,ad.wr_iot_interface_refs,3));
  ad.wr_iot_driver_owner.mutation_started=1;ad.vendor_count=2;
  assert(wr_iot_ref_open_finish(ref,&dev,ref->generation,ad.wr_iot_driver_owner.claim.serial,1));
  assert(wr_iot_bss_open_finish_observed(&ad.wr_iot_transition,ad.wr_iot_interface_refs,3,&dev,2,&ad.wr_iot_driver_owner.ticket,1));
  assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],7));
  if(mode==7||mode==11)ad.wr_iot_beacon_gates[2].active=1;
  if(mode==9)locked=0;
  int status=wr_iot_driver_first_beacon_wait(&ad,&dev,mode==10?0:3000);
  assert(!ad.wr_iot_transition_lock&&!ad.BcnRingLock&&ad.vendor_count==2);
  assert(m->phase==WR_REF_OWNED&&ref->phase==WR_REF_OWNED);
  if(mode==0||mode==11){assert(!status&&!ad.wr_iot_driver_owner.poisoned&&wait_calls==(mode==11?2:1));}
  else if(mode==10){assert(status==-EINVAL&&!ad.wr_iot_driver_owner.poisoned&&!wait_calls);}
  else assert(status==-EUCLEAN&&ad.wr_iot_driver_owner.poisoned&&ad.wr_iot_control_poisoned);
  assert(!ad.wr_iot_first_beacon.pending);
  assert(ad.wr_iot_driver_owner.receipt.first_beacon_confirmed==(mode==0||mode==11));
  if(mode==0||mode==11){
   assert(wr_iot_driver_request_leave(&ad,&dev,current));
   assert(ad.wr_iot_driver_owner.receipt.valid&&ad.wr_iot_driver_owner.receipt.first_beacon_confirmed==1);
  }
 }
 puts("PASS actual bounded first-beacon wait: shared budget, idle producer retry, identity/owner revalidation, no-progress/reject/cancel refusal and retained references on poison. Scheduler/time/MMIO injected; no RF proof.");
 return 0;
}
