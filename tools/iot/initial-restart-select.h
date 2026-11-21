#ifndef WR_IOT_INITIAL_RESTART_SELECT_H
#define WR_IOT_INITIAL_RESTART_SELECT_H
#include "precreated-idle-wire.h"
enum wr_iot_initial_selection {WR_INITIAL_SELECT_REFUSED=-1,
 WR_INITIAL_SELECT_NATIVE=0,WR_INITIAL_SELECT_ELIGIBLE=1};
/* Read-only selection, not ARM/OPEN permission. Once eligible, the physical
 * owner must repeat all admission checks under its own guard and fence.
 * Missing/stale driver proof is REFUSED, never permission for SDK fallback. */
enum wr_iot_initial_selection wr_iot_initial_restart_select(
 const unsigned char *,struct wr_iot_idle_result *);
/* Caller owns physical shutdown admission and service guard. Read-only fresh
 * proof for the selected lifetime; no claim, ARM or profile mutation. */
int wr_iot_initial_restart_selected_current(const unsigned char *,
 const struct wr_iot_idle_result *);
#endif
