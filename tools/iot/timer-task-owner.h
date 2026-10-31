/* One timer-task executor per adapter. All access holds TimerQLock.
 * Lives outside peer/timer memory; initialization is fresh-adapter only. */
#ifndef WR_IOT_TIMER_TASK_OWNER_H
#define WR_IOT_TIMER_TASK_OWNER_H
struct wr_iot_timer_task_owner {
 const void *running;
 unsigned long serial;
 unsigned int poisoned;
};
static inline void wr_iot_timer_task_owner_init(struct wr_iot_timer_task_owner *s){
 s->running=0;s->serial=0;s->poisoned=0;
}
static inline unsigned long wr_iot_timer_task_owner_begin(
 struct wr_iot_timer_task_owner *s,const void *timer){
 if(!s||!timer)return 0;
 if(s->poisoned||s->running||s->serial==~0UL){s->poisoned=1;return 0;}
 s->serial++;s->running=timer;return s->serial;
}
static inline int wr_iot_timer_task_owner_end(
 struct wr_iot_timer_task_owner *s,const void *timer,unsigned long serial){
 if(!s||!timer||!serial||s->poisoned||s->running!=timer||s->serial!=serial)return 0;
 s->running=0;return 1;
}
/* A true result concerns this executing task only, not pending kernel timers,
 * queued work, direct callbacks, rearm or adapter lifetime. */
static inline int wr_iot_timer_task_owner_idle_for(
 const struct wr_iot_timer_task_owner *s,const void *timer){
 return s&&timer&&!s->poisoned&&s->running!=timer;
}
#endif
