/* Caller holds BcnRingLock. One adapter-wide filter transaction; no MMIO here.
 * Tokens prevent stale completion from releasing a later transaction. */
#ifndef WR_IOT_BEACON_FILTER_OWNER_H
#define WR_IOT_BEACON_FILTER_OWNER_H
struct wr_iot_beacon_filter_owner {unsigned long serial,busy;};
static inline int wr_iot_beacon_filter_enter(struct wr_iot_beacon_filter_owner *o,unsigned long *token){
 if(!o||!token)return 0;
 *token=0;
 if(o->busy||o->serial==~0UL)return 0;
 o->serial++;o->busy=o->serial;*token=o->serial;return 1;
}
static inline int wr_iot_beacon_filter_leave(struct wr_iot_beacon_filter_owner *o,unsigned long token){
 if(!o||!token||o->busy!=token)return 0;
 o->busy=0;return 1;
}
#endif
