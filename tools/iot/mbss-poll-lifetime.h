/* Caller holds transition lock. OS queue/cancel/join receipts are supplied
 * by the binding; callback return alone never authorizes adapter release. */
#ifndef WR_IOT_MBSS_POLL_LIFETIME_H
#define WR_IOT_MBSS_POLL_LIFETIME_H
struct wr_iot_mbss_poll_lifetime {
 unsigned int stopped,pending,running,unjoined,attempts;
};
static inline void wr_iot_mbss_poll_init(struct wr_iot_mbss_poll_lifetime *s)
{s->stopped=s->pending=s->running=s->unjoined=s->attempts=0;}
static inline int wr_iot_mbss_poll_reserve(struct wr_iot_mbss_poll_lifetime *s)
{
 if(!s||s->stopped||s->pending||s->running||s->unjoined||s->attempts>=3U)return 0;
 s->pending=1;s->unjoined=1;s->attempts++;return 1;
}
static inline int wr_iot_mbss_poll_queue_result(
 struct wr_iot_mbss_poll_lifetime *s,int accepted)
{
 if(!s||!s->pending||!s->unjoined)return 0;
 if(!accepted){s->pending=0;if(!s->running)s->unjoined=0;}
 return 1;
}
/* Called by the running callback before it returns. The original unjoined
 * fence spans all rearms; even a refused rearm cannot remove that fence. */
static inline int wr_iot_mbss_poll_rearm(struct wr_iot_mbss_poll_lifetime *s)
{
 if(!s||s->stopped||!s->running||s->pending||!s->unjoined||s->attempts>=3U)return 0;
 s->pending=1;s->attempts++;return 1;
}
static inline int wr_iot_mbss_poll_begin(struct wr_iot_mbss_poll_lifetime *s)
{
 if(!s||!s->pending||s->running||!s->unjoined)return 0;
 s->pending=0;s->running=1;return !s->stopped;
}
static inline void wr_iot_mbss_poll_returned(struct wr_iot_mbss_poll_lifetime *s)
{if(s)s->running=0;}
static inline void wr_iot_mbss_poll_stop(struct wr_iot_mbss_poll_lifetime *s)
{if(s)s->stopped=1;}
/* OS synchronous join must have completed, including any pending callback. */
static inline int wr_iot_mbss_poll_joined(
 struct wr_iot_mbss_poll_lifetime *s,int os_joined)
{
 if(!s||!os_joined||s->running)return 0;
 s->pending=0;s->unjoined=0;return 1;
}
static inline int wr_iot_mbss_poll_release_ready(
 const struct wr_iot_mbss_poll_lifetime *s)
{return s&&s->stopped&&!s->pending&&!s->running&&!s->unjoined;}
#endif
