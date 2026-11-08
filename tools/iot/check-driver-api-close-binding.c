#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-owner.h"
typedef int INT;
typedef unsigned long ULONG;
typedef const void *PNET_DEV;
#define WDEV_NUM_MAX 1
struct wdev {PNET_DEV if_dev;};
typedef struct {
 int chip;PNET_DEV net_dev;
 struct {int BssidNum;struct {struct wdev wdev;} MBSSID[3];} ApCfg;
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 int wr_iot_transition_lock;
} RTMP_ADAPTER;
static int task,other,locks,unlocks;
#define current (&task)
#define IS_MT7603(ad) ((ad)->chip)
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(flags)=1;locks++;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);assert(flags);unlocks++;}while(0)
#include "driver-api-close-binding.inc"
int main(void){
 RTMP_ADAPTER ad={0};int main_dev,iot_dev;unsigned long gen=0;
 struct wr_iot_radio_ticket ticket={0};
 assert(wr_iot_driver_close_take_bound(&ad,&iot_dev,&ticket,&gen)==1);
 ad.wr_iot_close_owner.active=1;
 assert(wr_iot_driver_close_take_bound(&ad,&iot_dev,&ticket,&gen)==-1);
 ad.chip=1;ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;
 ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
 struct wr_iot_radio_transition *r=&ad.wr_iot_transition;
 wr_iot_radio_transition_init(r);r->phase=WR_RADIO_READY;r->main_ready=1;
 struct wr_iot_interface_ref *record=&ad.wr_iot_interface_refs[0];
 record->device=&iot_dev;record->generation=2;record->last_token=3;
 record->published=1;record->family=WR_REF_FAMILY_MBSS;record->phase=WR_REF_OWNED;
 assert(wr_iot_radio_begin_stop(r,2,&ad.wr_iot_close_owner.ticket));
 record->close_epoch=r->epoch;record->close_vendor_count=2;
 record->close_prior_phase=(int)ad.wr_iot_close_owner.ticket.prior_phase;
 record->close_prior_ready=ad.wr_iot_close_owner.ticket.prior_ready;
 ad.wr_iot_close_owner.device=&iot_dev;ad.wr_iot_close_owner.task=&other;
 ad.wr_iot_close_owner.generation=2;ad.wr_iot_close_owner.open_token=3;
 assert(wr_iot_driver_close_take_bound(&ad,&iot_dev,&ticket,&gen)==-1);
 ad.wr_iot_close_owner.task=current;
 unsigned long serial=r->serial;
 assert(!wr_iot_driver_close_take_bound(&ad,&iot_dev,&ticket,&gen));
 assert(gen==2&&ticket.serial==serial&&r->serial==serial);
 assert(wr_iot_driver_close_take_bound(&ad,&iot_dev,&ticket,&gen)==-1);
 assert(locks==unlocks&&ad.wr_iot_close_owner.active&&r->busy==WR_RADIO_BSS_CLOSE);
 puts("PASS exact CLOSE binding: no-owner legacy sentinel; active owner refusal never falls back; one same-ticket consume, balanced locks, no release");
}
