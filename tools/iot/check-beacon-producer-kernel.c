#include <assert.h>
#include <stdio.h>
#include "beacon-producer-gate.h"

#define WR_IOT_HOST_TEST 1
#define MT_MAC 1
#define RTMP_MAC_PCI 1
#define WDEV_NUM_MAX 4
typedef int INT;
static int locked, wakes, atomic_context;
#define RTMP_SEM_LOCK(p) do { (void)(p); assert(!locked); locked=1; } while(0)
#define RTMP_SEM_UNLOCK(p) do { (void)(p); assert(locked); locked=0; } while(0)
#define wake_up_all(p) do { (void)(p); wakes++; } while(0)
#define in_atomic() atomic_context
#define irqs_disabled() 0
#define READ_ONCE(x) (x)
#define msecs_to_jiffies(x) (x)
#define wait_event_timeout(q,c,t) ((void)(q),(void)(t),(c)?1:0)
typedef struct {
 int BcnRingLock, wr_iot_beacon_wait;
 struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[WDEV_NUM_MAX];
 struct {
  int BssidNum;
  struct { struct { int bBcnSntReq; } bcn_buf; } MBSSID[WDEV_NUM_MAX];
 } ApCfg;
} RTMP_ADAPTER;

#include "beacon-producer-kernel.h"

int main(void)
{
 RTMP_ADAPTER ad={0};
 struct wr_iot_beacon_producer_ticket first={0}, second={0};
 ad.ApCfg.BssidNum=3;
 wr_iot_beacon_gate_init(&ad.wr_iot_beacon_gates[1]);
 assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[1],1));
 ad.ApCfg.MBSSID[1].bcn_buf.bBcnSntReq=1;
 assert(wr_iot_bcn_producer_begin(&ad,1,&first));
 assert(wr_iot_bcn_producer_begin(&ad,1,&second));
 atomic_context=1;
 assert(!wr_iot_bcn_revoke_and_drain(&ad,1));
 assert(ad.wr_iot_beacon_gates[1].accepting);
 atomic_context=0;
 assert(!wr_iot_bcn_revoke_and_drain(&ad,1));
 assert(!ad.ApCfg.MBSSID[1].bcn_buf.bBcnSntReq);
 assert(!wr_iot_bcn_remove_ready(&ad,1));
 assert(!wr_iot_bcn_producer_begin(&ad,1,&(struct wr_iot_beacon_producer_ticket){0}));
 wr_iot_bcn_producer_end(&ad,1,&first);
 assert(!wakes);
 assert(!wr_iot_bcn_remove_ready(&ad,1));
 wr_iot_bcn_producer_end(&ad,1,&second);
 assert(wakes==1);
 assert(wr_iot_bcn_revoke_and_drain(&ad,1));
 assert(wr_iot_bcn_remove_ready(&ad,1));
 assert(!locked);
 puts("PASS kernel adapter binding: atomic refusal, revoke, producer drain, remove gate");
 return 0;
}
