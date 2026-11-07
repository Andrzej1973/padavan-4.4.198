/* Isolated MT7603 candidate binding; include only after rt_config.h.
 * The target's SEM and IRQ forms of BcnRingLock both use spin_lock_bh
 * because MULTI_CORE_SUPPORT is disabled. Do not install in production
 * without the recovery/PCI and late-report lifetime gates. */
#ifndef WR_IOT_BEACON_PRODUCER_KERNEL_H
#define WR_IOT_BEACON_PRODUCER_KERNEL_H
#ifndef WR_IOT_HOST_TEST
#include <linux/jiffies.h>
#include <linux/preempt.h>
#endif

#ifdef MULTI_CORE_SUPPORT
#error "Beacon producer binding needs a reviewed IRQ-safe lock for MULTI_CORE_SUPPORT"
#endif
#if defined(MT_MAC) && defined(RTMP_MAC_PCI)

static inline int wr_iot_bcn_producer_begin(RTMP_ADAPTER *ad, INT bss,
 struct wr_iot_beacon_producer_ticket *ticket)
{
 struct wr_iot_beacon_producer_gate *gate;
 int ok;
 if (!ad || !ticket || bss <= 0 || bss >= WDEV_NUM_MAX ||
     bss >= ad->ApCfg.BssidNum)
  return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 gate = &ad->wr_iot_beacon_gates[bss];
 ok = wr_iot_beacon_gate_begin(gate, gate->generation, ticket);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return ok;
}

static inline void wr_iot_bcn_producer_end(RTMP_ADAPTER *ad, INT bss,
 struct wr_iot_beacon_producer_ticket *ticket)
{
 int wake = 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 if (wr_iot_beacon_gate_end(&ad->wr_iot_beacon_gates[bss], ticket) &&
     !ad->wr_iot_beacon_gates[bss].active)
  wake = 1;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if (wake)
  wake_up_all(&ad->wr_iot_beacon_wait);
}

/* Caller is the process-context close owner, never a tasklet/IRQ handler.
 * Failed drain leaves the gate revoked and the close result unsuccessful. */
static inline int wr_iot_bcn_revoke_and_drain(RTMP_ADAPTER *ad, INT bss)
{
 struct wr_iot_beacon_producer_gate *gate;
 unsigned long generation;
 int ok;
 if (!ad || bss <= 0 || bss >= WDEV_NUM_MAX ||
     bss >= ad->ApCfg.BssidNum || in_atomic() || irqs_disabled())
  return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 gate = &ad->wr_iot_beacon_gates[bss];
 generation = gate->generation;
 ok = generation ? wr_iot_beacon_gate_revoke(gate, generation) :
      !gate->active;
 ad->ApCfg.MBSSID[bss].bcn_buf.bBcnSntReq = 0;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if (!ok)
  return 0;
 return wait_event_timeout(ad->wr_iot_beacon_wait,
  !READ_ONCE(gate->active), msecs_to_jiffies(3000)) != 0;
}

static inline int wr_iot_bcn_remove_ready(RTMP_ADAPTER *ad, INT bss)
{
 struct wr_iot_beacon_producer_gate *gate;
 int ok;
 if (!ad || bss <= 0 || bss >= WDEV_NUM_MAX ||
     bss >= ad->ApCfg.BssidNum)
  return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 gate = &ad->wr_iot_beacon_gates[bss];
 ok = !gate->generation ? !gate->active :
      wr_iot_beacon_gate_drained(gate, gate->generation);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return ok;
}
#endif /* MT_MAC && RTMP_MAC_PCI */
#endif
