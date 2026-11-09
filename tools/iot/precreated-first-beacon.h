/* Staged host submission receipt for a reserved BSS; NOT RF/TxS completion.
 * All access requires one caller-owned lock and pinned adapter/netdev lifetime.
 * Arm only after loaded-profile/cold-slot admission. The periodic producer must
 * capture this identity BEFORE building and report only a positively accepted
 * host submission, never VOID builder return or a read of current identity.
 * Host submission is not DMA execution, firmware ACK or over-air delivery.
 * No production hook is installed. Existing late-TxS gates remain mandatory. */
#ifndef WR_IOT_PRECREATED_FIRST_BEACON_H
#define WR_IOT_PRECREATED_FIRST_BEACON_H
struct wr_iot_first_beacon_identity {
 const void *device;
 unsigned long netdev_generation,producer_generation,radio_epoch,open_serial;
 unsigned long long request_generation;
};
struct wr_iot_first_beacon {
 struct wr_iot_first_beacon_identity identity;
 unsigned long long last_request;
 unsigned int pending,submitted;
};
static inline int wr_iot_first_beacon_identity_valid(
 const struct wr_iot_first_beacon_identity *id)
{
 return id&&id->device&&id->netdev_generation&&id->producer_generation&&
  id->radio_epoch&&id->open_serial&&id->request_generation;
}
static inline int wr_iot_first_beacon_identity_equal(
 const struct wr_iot_first_beacon_identity *a,
 const struct wr_iot_first_beacon_identity *b)
{
 return wr_iot_first_beacon_identity_valid(a)&&
  wr_iot_first_beacon_identity_valid(b)&&a->device==b->device&&
  a->netdev_generation==b->netdev_generation&&
  a->producer_generation==b->producer_generation&&
  a->radio_epoch==b->radio_epoch&&a->open_serial==b->open_serial&&
  a->request_generation==b->request_generation;
}
static inline int wr_iot_first_beacon_arm(struct wr_iot_first_beacon *state,
 const struct wr_iot_first_beacon_identity *id)
{
 if(!state||state->pending||!wr_iot_first_beacon_identity_valid(id)||
    id->request_generation<=state->last_request)return 0;
 state->identity=*id;state->last_request=id->request_generation;
 state->pending=1;state->submitted=0;return 1;
}
/* Identity is the producer's captured token, not a synthetic firmware cookie.
 * Late or rejected submissions cannot satisfy a later activation request. */
static inline int wr_iot_first_beacon_submitted(struct wr_iot_first_beacon *state,
 const struct wr_iot_first_beacon_identity *producer,int accepted)
{
 if(!state||!state->pending||state->submitted||accepted!=1||
    !wr_iot_first_beacon_identity_equal(&state->identity,producer))return 0;
 state->submitted=1;return 1;
}
/* Consume once after revalidating actual ownership/profile/epoch. A stale
 * consumer cannot cancel a newer request. An invalid current owner consumes
 * its own receipt and requires fail-closed recovery, not global refresh. */
static inline int wr_iot_first_beacon_finish(struct wr_iot_first_beacon *state,
 const struct wr_iot_first_beacon_identity *request,int current_owner)
{
 int ready;
 if(!state||!state->pending||
    !wr_iot_first_beacon_identity_equal(&state->identity,request))return 0;
 ready=state->submitted&&current_owner==1;
 state->pending=state->submitted=0;return ready;
}
/* Called by the actual bounded wait/cancel owner; this helper has no clock.
 * Do not clear last_request or reinitialize live state to recycle identity. */
static inline int wr_iot_first_beacon_expire(struct wr_iot_first_beacon *state,
 const struct wr_iot_first_beacon_identity *request)
{
 if(!state||!state->pending||
    !wr_iot_first_beacon_identity_equal(&state->identity,request))return 0;
 state->pending=state->submitted=0;return 1;
}
#endif
