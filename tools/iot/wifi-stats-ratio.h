/* Diagnostic counters are 32-bit. Widen before addition and scaling. */
#ifndef WR_WIFI_STATS_RATIO_H
#define WR_WIFI_STATS_RATIO_H
#include <linux/math64.h>
static inline unsigned long wr_wifi_stats_ratio(u64 failures, u64 successes,
                                              unsigned int scale)
{
 u64 total = failures + successes;
 return total ? (unsigned long)div64_u64(failures * scale, total) : 0;
}
#endif
