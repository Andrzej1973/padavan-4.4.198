#ifndef WR_RSSI_KERNEL_H
#define WR_RSSI_KERNEL_H
#ifndef __KERNEL__
#error RSSI kernel observer requires the actual kernel build environment
#endif
#include <linux/spinlock.h>
#include <linux/string.h>
#include <linux/random.h>
#include "rssi-record.h"
#include "rssi-query-request.h"
/* One instance per adapter. Initialize before publishing the adapter and
 * quiesce producers/readers before teardown. Do not reset a live instance.
 * Lock order: station-table lock may precede this observer lock; never call
 * station-table functions, allocate, log, or copy to userspace while holding
 * this observer lock. Snapshot buffers belong to kernel callers. */
struct wr_rssi_kernel {
 spinlock_t lock;
 unsigned long long session[2];
 struct wr_rssi_records records;
};
struct wr_rssi_snapshot_meta {
 unsigned long long sequence,overwritten,session[2];
};
static inline void wr_rssi_kernel_init(struct wr_rssi_kernel *observer)
{
 memset(&observer->records,0,sizeof observer->records);
 spin_lock_init(&observer->lock);
 /* Instance tag, not an authentication secret. Zero remains invalid for reads. */
 get_random_bytes(observer->session,sizeof observer->session);
}
static inline int wr_rssi_kernel_append(struct wr_rssi_kernel *observer,
 const struct wr_rssi_record *record)
{
 unsigned long flags;int result;
 if(!observer||!record)return 0;
 spin_lock_irqsave(&observer->lock,flags);
 result=wr_rssi_record_append(&observer->records,record);
 spin_unlock_irqrestore(&observer->lock,flags);
 return result;
}
static inline int wr_rssi_kernel_begin(struct wr_rssi_kernel *observer,
 struct wr_rssi_record *identity)
{
 unsigned long flags;int result;
 if(!observer||!identity)return 0;
 spin_lock_irqsave(&observer->lock,flags);
 result=wr_rssi_record_begin(&observer->records,identity);
 spin_unlock_irqrestore(&observer->lock,flags);
 return result;
}
static inline int wr_rssi_kernel_snapshot(struct wr_rssi_kernel *observer,
 unsigned long long after,struct wr_rssi_record *output,unsigned int capacity,
 struct wr_rssi_snapshot_meta *meta)
{
 unsigned long flags;int result;
 if(!observer||!meta)return -1;
 spin_lock_irqsave(&observer->lock,flags);
 result=wr_rssi_record_read(&observer->records,after,output,capacity);
 if(result>=0){meta->sequence=observer->records.sequence;
              meta->overwritten=observer->records.overwritten;
              meta->session[0]=observer->session[0];
              meta->session[1]=observer->session[1];}
 spin_unlock_irqrestore(&observer->lock,flags);
 return result;
}
/* Query fields are decoded before this call. -2 denotes instance mismatch;
 * -1 denotes invalid bounds/cursor. Neither failure modifies output/meta. */
static inline int wr_rssi_kernel_query(struct wr_rssi_kernel *observer,
 const struct wr_rssi_query_request *request,struct wr_rssi_record *output,
 struct wr_rssi_snapshot_meta *meta)
{
 unsigned long flags;int result;
 if(!observer||!request||!meta||!output)return -1;
 spin_lock_irqsave(&observer->lock,flags);
 if(!wr_rssi_query_session_matches(request,observer->session))result=-2;
 else {
  result=wr_rssi_record_read(&observer->records,request->after,output,request->capacity);
  if(result>=0) {
   meta->sequence=observer->records.sequence;
   meta->overwritten=observer->records.overwritten;
   meta->session[0]=observer->session[0];meta->session[1]=observer->session[1];
  }
 }
 spin_unlock_irqrestore(&observer->lock,flags);
 return result;
}
#endif
