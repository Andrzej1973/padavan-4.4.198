/* Adapter lifetime is caller-owned. Every operation holds transition lock.
 * A reaper lease excludes admission and other reapers while joining work.
 * Stop is permanent for this adapter allocation, including empty owners.
 * This gate is not itself a work join or adapter release receipt. */
#ifndef WR_IOT_MBSS_REAPER_GATE_H
#define WR_IOT_MBSS_REAPER_GATE_H
struct wr_iot_mbss_reaper_gate {
 unsigned int stopped,reaping,submissions,poisoned;
};
static inline void wr_iot_mbss_reaper_gate_init(struct wr_iot_mbss_reaper_gate *g)
{g->stopped=0;g->reaping=0;g->submissions=0;g->poisoned=0;}
static inline int wr_iot_mbss_submission_enter(struct wr_iot_mbss_reaper_gate *g)
{
 if(!g||g->stopped||g->reaping||g->poisoned)return 0;
 if(g->submissions==~0U){g->poisoned=1;return 0;}
 g->submissions++;return 1;
}
static inline int wr_iot_mbss_submission_leave(struct wr_iot_mbss_reaper_gate *g)
{
 if(!g||!g->submissions){if(g)g->poisoned=1;return 0;}
 g->submissions--;return 1;
}
static inline void wr_iot_mbss_reaper_stop(struct wr_iot_mbss_reaper_gate *g)
{if(g)g->stopped=1;}
static inline int wr_iot_mbss_reaper_enter(struct wr_iot_mbss_reaper_gate *g)
{
 if(!g||g->poisoned||g->reaping||g->submissions)return 0;
 g->reaping=1;return 1;
}
static inline int wr_iot_mbss_reaper_leave(struct wr_iot_mbss_reaper_gate *g)
{
 if(!g||!g->reaping){if(g)g->poisoned=1;return 0;}
 g->reaping=0;return 1;
}
static inline int wr_iot_mbss_reaper_idle(const struct wr_iot_mbss_reaper_gate *g)
{return g&&!g->poisoned&&!g->reaping&&!g->submissions;}
#endif
