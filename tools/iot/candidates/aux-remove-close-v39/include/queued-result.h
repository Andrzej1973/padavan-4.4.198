/* Candidate kernel-only shared result. Not bound to production queue/issuer.
 * Each caller of an operation must retain a reference throughout that call.
 * Reserve a queue ref BEFORE enqueue; release it on rejection or after worker
 * cleanup. Waiter cancellation is not proof that running hardware work stopped.
 */
#ifndef WR_IOT_QUEUED_RESULT_H
#define WR_IOT_QUEUED_RESULT_H
#ifndef WR_IOT_RESULT_TEST
#include <linux/slab.h>
#include <linux/kref.h>
#include <linux/spinlock.h>
#include <linux/completion.h>
#endif
enum wr_iot_work_state {
 WR_IOT_WORK_QUEUED, WR_IOT_WORK_RUNNING, WR_IOT_WORK_DONE,
 WR_IOT_WORK_CANCELLED, WR_IOT_WORK_UNCERTAIN
};
struct wr_iot_queued_result {
 struct kref refs;
 spinlock_t lock;
 struct completion done;
 enum wr_iot_work_state state;
 int status;
};
static inline void wr_iot_result_release(struct kref *ref)
{
 struct wr_iot_queued_result *r=container_of(ref,struct wr_iot_queued_result,refs);
 kfree(r);
}
static inline struct wr_iot_queued_result *wr_iot_result_alloc(void)
{
 struct wr_iot_queued_result *r=kzalloc(sizeof(*r),GFP_KERNEL);
 if(!r)return NULL;
 kref_init(&r->refs);spin_lock_init(&r->lock);init_completion(&r->done);
 r->state=WR_IOT_WORK_QUEUED;r->status=-1;
 return r;
}
static inline void wr_iot_result_get(struct wr_iot_queued_result *r)
{ kref_get(&r->refs); }
static inline void wr_iot_result_put(struct wr_iot_queued_result *r)
{ kref_put(&r->refs,wr_iot_result_release); }
static inline int wr_iot_result_start(struct wr_iot_queued_result *r)
{
 unsigned long flags;int start=0;
 spin_lock_irqsave(&r->lock,flags);
 if(r->state==WR_IOT_WORK_QUEUED){r->state=WR_IOT_WORK_RUNNING;start=1;}
 spin_unlock_irqrestore(&r->lock,flags);
 return start;
}
static inline int wr_iot_result_finish(struct wr_iot_queued_result *r,int status)
{
 unsigned long flags;int changed=0;
 spin_lock_irqsave(&r->lock,flags);
 if(r->state==WR_IOT_WORK_RUNNING){
  r->state=WR_IOT_WORK_DONE;r->status=status;changed=1;
 }
 spin_unlock_irqrestore(&r->lock,flags);
 if(changed)complete_all(&r->done);
 return changed;
}
/* Used on timeout, rejected dispatch, or shutdown before releasing queue ref.
 * QUEUED cancellation prevents start. RUNNING cancellation is uncertain.
 */
static inline int wr_iot_result_cancel(struct wr_iot_queued_result *r)
{
 unsigned long flags;int changed=0;
 spin_lock_irqsave(&r->lock,flags);
 if(r->state==WR_IOT_WORK_QUEUED||r->state==WR_IOT_WORK_RUNNING){
  r->state=r->state==WR_IOT_WORK_QUEUED?WR_IOT_WORK_CANCELLED:WR_IOT_WORK_UNCERTAIN;
  r->status=-1;changed=1;
 }
 spin_unlock_irqrestore(&r->lock,flags);
 if(changed)complete_all(&r->done);
 return changed;
}
static inline enum wr_iot_work_state wr_iot_result_read(
 struct wr_iot_queued_result *r,int *status)
{
 unsigned long flags;enum wr_iot_work_state state;
 spin_lock_irqsave(&r->lock,flags);state=r->state;*status=r->status;
 spin_unlock_irqrestore(&r->lock,flags);return state;
}
#endif
