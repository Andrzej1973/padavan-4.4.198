/* Isolated all-child teardown contract. No vendor/PCI binding yet.
 * All calls require the shared adapter transition lock. This records only
 * caller-proven events; it neither unregisters devices nor drains callbacks. */
#ifndef WR_IOT_ALL_CHILD_TEARDOWN_H
#define WR_IOT_ALL_CHILD_TEARDOWN_H

#define WR_CHILD_APCLI   (1U << 0)
#define WR_CHILD_WDS     (1U << 1)
#define WR_CHILD_MBSS    (1U << 2)
#define WR_CHILD_MONITOR (1U << 3)
#define WR_CHILD_ALL (WR_CHILD_APCLI | WR_CHILD_WDS | WR_CHILD_MBSS | WR_CHILD_MONITOR)

enum wr_child_teardown_phase {
 WR_CHILD_IDLE, WR_CHILD_DRAINING, WR_CHILD_DONE, WR_CHILD_POISONED
};
struct wr_child_teardown {
 unsigned int expected, closed, completed;
 enum wr_child_teardown_phase phase;
};
static inline void wr_child_teardown_init(struct wr_child_teardown *t){
 t->expected=0;t->closed=0;t->completed=0;t->phase=WR_CHILD_IDLE;
}
/* Caller has fenced all open/reset and new callbacks before this point.
 * expected is the exact set of currently published child families. */
static inline int wr_child_teardown_begin(struct wr_child_teardown *t,
 unsigned int expected, int admissions_fenced){
 if(!t||t->phase!=WR_CHILD_IDLE||!admissions_fenced||
    (expected&~WR_CHILD_ALL))return 0;
 t->expected=expected;t->closed=0;t->completed=0;
 t->phase=expected?WR_CHILD_DRAINING:WR_CHILD_DONE;
 return 1;
}
/* Record checked close of every active interface in this family and a joined
 * recovery owner, before any family remove/deinit begins. A caller must not
 * claim this merely because ndo_stop returned or a stop was requested. */
static inline int wr_child_teardown_close_done(struct wr_child_teardown *t,
 unsigned int family,int checked_close_and_join_proven){
 if(!t||t->phase!=WR_CHILD_DRAINING||!family||
    (family&(family-1U))||(family&~t->expected)||
    (family&t->closed)||!checked_close_and_join_proven)return 0;
 t->closed|=family;return 1;
}
/* Mark only after the entire family is retired, including callback refs.
 * A family with multiple BSS cannot be marked after just one netdev free. */
static inline int wr_child_teardown_complete(struct wr_child_teardown *t,
 unsigned int family){
 if(!t||t->phase!=WR_CHILD_DRAINING||!family||
    (family&(family-1U))||(family&~t->closed)||
    (family&t->completed))return 0;
 t->completed|=family;
 if(t->completed==t->expected)t->phase=WR_CHILD_DONE;
 return 1;
}
/* Failure after mutation is terminal for this transaction. The caller must
 * retain adapter resources; PCI remove cannot simply continue or retry. */
static inline void wr_child_teardown_fail(struct wr_child_teardown *t){
 if(t&&t->phase==WR_CHILD_DRAINING)t->phase=WR_CHILD_POISONED;
}
/* Only an entirely unmutated attempt may be canceled. The caller must prove
 * that no vendor/kernel mutation occurred even when completed is zero. */
static inline int wr_child_teardown_abort_unmutated(
 struct wr_child_teardown *t,int no_mutation){
 if(!t||t->phase!=WR_CHILD_DRAINING||t->closed||t->completed||
    !no_mutation)return 0;
 wr_child_teardown_init(t);return 1;
}
/* The caller must separately prove every TX, DMA, vendor worker and kernel
 * callback is quiescent and the main netdev is ready for final detach. */
static inline int wr_child_teardown_may_free_adapter(
 const struct wr_child_teardown *t,int all_paths_quiescent){
 return t&&t->phase==WR_CHILD_DONE&&all_paths_quiescent;
}
#endif
