/* Model only. Every producer and close/reopen access requires one shared
 * IRQ-safe lock. The lease spans the scheduling API call, not task execution.
 * Adapter lifetime and actual callback join remain caller obligations. */
#ifndef WR_IOT_TASKLET_SCHEDULE_OWNER_H
#define WR_IOT_TASKLET_SCHEDULE_OWNER_H
struct wr_iot_tasklet_schedule_owner {unsigned int blocked,inflight,poisoned;};
static inline void wr_iot_tasklet_schedule_init(struct wr_iot_tasklet_schedule_owner *s){
 s->blocked=1;s->inflight=0;s->poisoned=0;
}
static inline int wr_iot_tasklet_schedule_enter(struct wr_iot_tasklet_schedule_owner *s){
 if(!s||s->blocked||s->poisoned)return 0;
 if(s->inflight==~0U){s->poisoned=1;s->blocked=1;return 0;}
 s->inflight++;return 1;
}
static inline int wr_iot_tasklet_schedule_leave(struct wr_iot_tasklet_schedule_owner *s){
 if(!s||!s->inflight){if(s){s->poisoned=1;s->blocked=1;}return 0;}
 s->inflight--;return 1;
}
static inline void wr_iot_tasklet_schedule_block(struct wr_iot_tasklet_schedule_owner *s){
 if(s)s->blocked=1;
}
static inline int wr_iot_tasklet_schedule_may_join(const struct wr_iot_tasklet_schedule_owner *s){
 return s&&s->blocked&&!s->inflight&&!s->poisoned;
}
/* Caller proves newly initialized tasklet storage and prior callback join.
 * Never use as a generic failed-close recovery or live-state reset. */
static inline int wr_iot_tasklet_schedule_open(struct wr_iot_tasklet_schedule_owner *s,
 int initialized,int prior_joined){
 if(!wr_iot_tasklet_schedule_may_join(s)||!initialized||!prior_joined)return 0;
 s->blocked=0;return 1;
}
#endif
