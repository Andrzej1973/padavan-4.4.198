/* Isolated per-BSS teardown milestones. Caller holds the adapter transition
 * lock for all state changes and separately proves each external operation.
 * This does not unregister devices or wait for vendor callbacks. */
#ifndef WR_IOT_MBSS_RETIREMENT_H
#define WR_IOT_MBSS_RETIREMENT_H
enum wr_bss_retire_stage {
 WR_BSS_ABSENT, WR_BSS_LIVE, WR_BSS_REMOVING,
 WR_BSS_BEACON_DONE, WR_BSS_KERNEL_DONE, WR_BSS_VENDOR_DONE
};
struct wr_bss_retirement {
 unsigned long generation;
 enum wr_bss_retire_stage stage;
};
static inline void wr_bss_retirement_init(struct wr_bss_retirement *b){
 b->generation=0;b->stage=WR_BSS_ABSENT;
}
static inline int wr_bss_retirement_publish(struct wr_bss_retirement *b,
 unsigned long generation){
 if(!b||b->stage!=WR_BSS_ABSENT||!generation)return 0;
 b->generation=generation;b->stage=WR_BSS_LIVE;return 1;
}
static inline int wr_bss_retirement_begin(struct wr_bss_retirement *b,
 unsigned long generation,int admissions_fenced){
 if(!b||b->generation!=generation||!generation||!admissions_fenced||
    b->stage!=WR_BSS_LIVE)return 0;
 b->stage=WR_BSS_REMOVING;return 1;
}
/* Only a proven unmutated refusal may restore LIVE. */
static inline int wr_bss_retirement_abort_unmutated(
 struct wr_bss_retirement *b,unsigned long generation,int no_mutation){
 if(!b||b->generation!=generation||!generation||!no_mutation||
    b->stage!=WR_BSS_REMOVING)return 0;
 b->stage=WR_BSS_LIVE;return 1;
}
static inline int wr_bss_retirement_beacon_done(
 struct wr_bss_retirement *b,unsigned long generation){
 if(!b||b->generation!=generation||!generation||
    b->stage!=WR_BSS_REMOVING)return 0;
 b->stage=WR_BSS_BEACON_DONE;return 1;
}
static inline int wr_bss_retirement_kernel_done(
 struct wr_bss_retirement *b,unsigned long generation){
 if(!b||b->generation!=generation||!generation||
    b->stage!=WR_BSS_BEACON_DONE)return 0;
 b->stage=WR_BSS_KERNEL_DONE;return 1;
}
static inline int wr_bss_retirement_vendor_done(
 struct wr_bss_retirement *b,unsigned long generation){
 if(!b||b->generation!=generation||!generation||
    b->stage!=WR_BSS_KERNEL_DONE)return 0;
 b->stage=WR_BSS_VENDOR_DONE;return 1;
}
/* A retry may resume from its recorded stage; destructive operations must
 * never be repeated. The caller still owns the failure/retry lifetime. */
static inline int wr_bss_retirement_needs_beacon(
 const struct wr_bss_retirement *b,unsigned long generation){
 return b&&generation&&b->generation==generation&&
        b->stage==WR_BSS_REMOVING;
}
static inline int wr_bss_retirement_family_done(
 const struct wr_bss_retirement *slots,unsigned int count){
 unsigned int i;
 if(!slots)return 0;
 for(i=0;i<count;i++)
  if(slots[i].stage!=WR_BSS_ABSENT&&slots[i].stage!=WR_BSS_VENDOR_DONE)
   return 0;
 return 1;
}
/* Slot reuse requires independently proven callback quiescence. */
static inline int wr_bss_retirement_release(struct wr_bss_retirement *b,
 unsigned long generation,int callbacks_quiescent){
 if(!b||b->generation!=generation||!generation||!callbacks_quiescent||
    b->stage!=WR_BSS_VENDOR_DONE)return 0;
 wr_bss_retirement_init(b);return 1;
}
#endif
