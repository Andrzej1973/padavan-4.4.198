/* Host contract for per-BSS beacon/TIM preparation lifetime.
 * All operations are performed under BcnRingLock in a future driver binding.
 * Waiting for a drain must happen after releasing that lock. */
#ifndef WR_IOT_BEACON_PRODUCER_GATE_H
#define WR_IOT_BEACON_PRODUCER_GATE_H

struct wr_iot_beacon_producer_gate {
 unsigned long generation;
 unsigned int active;
 int accepting;
};

static inline void wr_iot_beacon_gate_init(struct wr_iot_beacon_producer_gate *g)
{
 g->generation=0;g->active=0;g->accepting=0;
}

/* Reopen is forbidden until every producer of the old generation exits. */
static inline int wr_iot_beacon_gate_open(struct wr_iot_beacon_producer_gate *g,
                                         unsigned long generation)
{
 if(!g||!generation||g->accepting||g->active||
    generation<=g->generation)return 0;
 g->generation=generation;g->accepting=1;
 return 1;
}

/* Take the pin before reading BeaconPkt or TimPkt. */
static inline int wr_iot_beacon_gate_begin(struct wr_iot_beacon_producer_gate *g,
                                          unsigned long generation)
{
 if(!g||!g->accepting||g->generation!=generation||
    g->active==(unsigned int)-1)return 0;
 g->active++;
 return 1;
}

/* Revoke under the same lock as begin and final hardware submission. */
static inline int wr_iot_beacon_gate_revoke(struct wr_iot_beacon_producer_gate *g,
                                           unsigned long generation)
{
 if(!g||!g->accepting||g->generation!=generation)return 0;
 g->accepting=0;
 return 1;
}

/* Final submission is permitted only while this generation is open. */
static inline int wr_iot_beacon_gate_submit(const struct wr_iot_beacon_producer_gate *g,
                                           unsigned long generation)
{
 return g&&g->accepting&&g->active&&g->generation==generation;
}

/* End after final submit or cancel, including every early-return path. */
static inline int wr_iot_beacon_gate_end(struct wr_iot_beacon_producer_gate *g,
                                        unsigned long generation)
{
 if(!g||!g->active||g->generation!=generation)return 0;
 g->active--;
 return 1;
}

/* Buffer deinit additionally requires DMA, TxS and late-report proofs. */
static inline int wr_iot_beacon_gate_drained(const struct wr_iot_beacon_producer_gate *g,
                                            unsigned long generation)
{
 return g&&!g->accepting&&!g->active&&g->generation==generation;
}
#endif
