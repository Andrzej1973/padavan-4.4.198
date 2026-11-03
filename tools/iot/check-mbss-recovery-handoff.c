#include <assert.h>
#define INT int
typedef struct {int pin;} RTMP_ADAPTER;
typedef void *PNET_DEV;
struct wr_iot_radio_ticket {unsigned long serial;};
static int owner_result,caller_result,submits,closes,schedules;
static RTMP_ADAPTER *expected_ad;
static PNET_DEV expected_dev;
static const struct wr_iot_radio_ticket *expected_ticket;
static int wr_iot_mbss_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev,unsigned long gen)
{assert(ad==expected_ad&&dev==expected_dev&&gen==9&&ad->pin);submits++;return owner_result;}
static int wr_iot_mbss_recovery_submit_close(RTMP_ADAPTER *ad,PNET_DEV dev,unsigned long gen,const struct wr_iot_radio_ticket *ticket)
{assert(ad==expected_ad&&dev==expected_dev&&gen==9&&ticket==expected_ticket&&ad->pin);closes++;return owner_result;}
static int wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad)
{assert(ad==expected_ad&&ad->pin);schedules++;return caller_result;}
#include "mbss-recovery-handoff.inc"
int main(void){
 RTMP_ADAPTER ad={1};int dev;struct wr_iot_radio_ticket ticket={17};
 expected_ad=&ad;expected_dev=&dev;expected_ticket=&ticket;
 for(int close=0;close<2;close++)for(int owner=-1;owner<=1;owner++)for(int caller=-1;caller<=0;caller++){
  owner_result=owner;caller_result=caller;submits=closes=schedules=0;
  int result=wr_iot_mbss_recovery_handoff(&ad,&dev,9,close?&ticket:0);
  assert(result==(owner<0?-1:owner==0&&caller==0?0:1));
  assert(submits==!close&&closes==close&&schedules==(owner>=0)&&ad.pin==1);
 }
 return 0;
}
