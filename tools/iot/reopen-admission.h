/* Fresh post-CLOSE configuration admission. Never an initial-idle substitute
 * or permission to release descriptors. Caller retains completed active-stop. */
#ifndef WR_IOT_REOPEN_ADMISSION_H
#define WR_IOT_REOPEN_ADMISSION_H
#include "active-stop.h"
/* Caller can retain this read-only predicate only while old stopped context
 * remains alive. Network setup changes OFF gates, so its later phases need a
 * distinct CLOSED-only witness, not this full OFF predicate. */
int wr_iot_reopen_closed_current(const struct wr_iot_start_runner *,
 const struct wr_iot_active_stop *);
#include "reopen-witness.h"
/* Capture only from fully observed completed OFF. No pointers into old owner. */
int wr_iot_reopen_witness_take(struct wr_iot_reopen_witness *,
 const struct wr_iot_start_runner *,const struct wr_iot_active_stop *);
/* Capture after a submitted startup OPEN was CLOSED and its rollback completed.
 * Requires fresh fully disabled network state and exact new CLOSE identity. */
int wr_iot_reopen_recovered_witness_take(struct wr_iot_reopen_witness *,
 const struct wr_iot_start_runner *);
/* Guard required. Allows staged network state but requires old BSS CLOSED.
 * Stop using this witness before submitting new OPEN; retain it for recovery. */
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness *);
#endif
