/* Caller serializes the persistent slot counter and entry with MacTabLock.
 * Zero is invalid. Exhaustion is permanent for this adapter lifetime. */
#ifndef WR_IOT_ASSOC_GENERATION_H
#define WR_IOT_ASSOC_GENERATION_H
static inline unsigned int wr_assoc_generation_next(unsigned int *counter)
{
 if (*counter == ~0U) return 0;
 return ++*counter;
}
static inline int wr_assoc_generation_matches(unsigned int queued,
 unsigned int current_gen, int valid, int same_mac)
{
 return valid && same_mac && queued != 0 && queued == current_gen;
}
#endif
