#ifndef WR_TMP_UPLOAD_POLICY_H
#define WR_TMP_UPLOAD_POLICY_H
#define WR_TMP_MIB (1024ULL * 1024ULL)
/* No allocation or remount: decide a ceiling from a single memory snapshot. */
static int wr_tmp_upload_plan(unsigned long long current,
 unsigned long long used, unsigned long long available,
 unsigned long long *desired)
{
 unsigned long long budget, cap = 50 * WR_TMP_MIB;
 if (!desired || used > current) return -1;
 *desired = current;
 if (current >= cap) return 2;
 if (available <= 16 * WR_TMP_MIB) return -2;
 budget = available - 16 * WR_TMP_MIB;
 /* Saturate before addition; memory counters must not wrap the ceiling. */
 if (used >= cap || budget >= cap - used) *desired = cap;
 else *desired = ((used + budget) / WR_TMP_MIB) * WR_TMP_MIB;
 if (*desired <= current) { *desired = current; return -2; }
 return 1;
}
#endif
