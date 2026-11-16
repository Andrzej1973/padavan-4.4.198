#ifndef WR_IOT_RESTART_INITIAL_PARENT_H
#define WR_IOT_RESTART_INITIAL_PARENT_H
#include "restart-restore.h"
/* Restart parent only, not START/ACTIVE proof. before_start=1 additionally
 * checks the current never-opened Main/ra2 identity. Caller holds admission. */
int wr_iot_restart_initial_parent_current(struct wr_iot_restart_restore *,int before_start);
#endif
