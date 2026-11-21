#include "physical-stop-record.h"
/* Kernel-only extra-reference bundle. Caller serializes slot access under the
 * adapter-owned lock, but acquire/drop run outside locks. This does not pin
 * PCI hardware by itself: remove must refuse while the record/bundle is owned.
 * Only unpublished local bundles may be copied into/out of an adapter slot. */
#include "physical-stop-pin-types.h"
static inline int wr_iot_physical_stop_pins_acquire(struct wr_iot_physical_stop_pins *p,
 struct task_struct *task,struct net_device *device)
{
 if(!p||p->task||p->device||p->module||!task||task!=current||!device)return 0;
 if(!try_module_get(THIS_MODULE))return 0;
 get_task_struct(task);dev_hold(device);
 p->task=task;p->device=device;p->module=1;return 1;
}
/* May be used only after exact ARMED cancellation or COMPLETE release detached
 * the bundle under the lock. A failed/RUNNING record retains its references.
 * Clear first so dev_put callbacks cannot find a reusable owned local bundle. */
static inline int wr_iot_physical_stop_pins_drop(struct wr_iot_physical_stop_pins *p)
{
 struct task_struct *task;struct net_device *device;
 if(!p||!p->module||!p->task||!p->device)return 0;
 task=p->task;device=p->device;
 p->module=0;p->task=NULL;p->device=NULL;
 dev_put(device);put_task_struct(task);module_put(THIS_MODULE);return 1;
}
/* Caller already owns RTNL/adapter lifetime and MacTabLock. local was acquired
 * outside locks. Admission identity/CLOSED checks must run in their existing
 * serialized owner before this transfer; this helper does not invent proof. */
static inline int wr_iot_physical_stop_pins_publish(struct wr_iot_physical_stop_pins *slot,
 struct wr_iot_physical_stop_pins *local,struct wr_iot_physical_stop_record *record,
 unsigned long long epoch,unsigned long long generation,unsigned long long token,
 unsigned long long closed_serial,const unsigned char *nonce,
 const struct wr_iot_peer_close_executor *executor)
{
 if(!slot||!local||slot==local||slot->module||slot->task||slot->device||
    local->module!=1||local->task!=current||!local->device||
    !wr_iot_physical_stop_arm(record,epoch,generation,token,closed_serial,
                              nonce,local->task,executor))return 0;
 *slot=*local;local->module=0;local->task=NULL;local->device=NULL;return 1;
}
/* Caller keeps a separate synchronous ioctl/module/adapter pin until this
 * detached local bundle is dropped outside the lock. Never access an adapter
 * after releasing its final reference. Failed/RUNNING attempts stay owned. */
static inline int wr_iot_physical_stop_pins_detach(struct wr_iot_physical_stop_pins *slot,
 struct wr_iot_physical_stop_pins *local,struct wr_iot_physical_stop_record *record,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,int cancel)
{
 int ok;
 if(!slot||!local||slot==local||local->module||local->task||local->device||
    slot->module!=1||slot->task!=current||!slot->device||
    !record||record->task!=slot->task|| (cancel!=0&&cancel!=1))return 0;
 ok=cancel?wr_iot_physical_stop_cancel(record,serial,epoch,generation,nonce,current):
           wr_iot_physical_stop_release(record,serial,epoch,generation,nonce,current);
 if(!ok)return 0;
 *local=*slot;slot->module=0;slot->task=NULL;slot->device=NULL;return 1;
}
/* Read under the SAME MacTabLock as publication/detach, with RTNL held across
 * detach plus reference return. Do not sample this under transition lock alone.
 * Partial/inconsistent bundle state refuses adapter retirement as well. */
static inline int wr_iot_physical_stop_blocks_retirement(
 const struct wr_iot_physical_stop_record *record,
 const struct wr_iot_physical_stop_pins *slot)
{
 return !record||!slot||record->phase!=WR_PHYS_STOP_IDLE||record->task||
        slot->module||slot->task||slot->device;
}
