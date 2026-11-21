#ifndef WR_IOT_RESTART_GUEST_UP_H
#define WR_IOT_RESTART_GUEST_UP_H
#include "restart-main-up.h"
/* Fixed ra1 only, requires ra0 UP. Caller records attempt before calling;
 * transport outcome never proves loaded BSS/security or isolation readiness. */
enum wr_iot_restart_up_result wr_iot_restart_guest_up(void);
/* Fixed ra1 DOWN, preserving unrelated flags; no internal retry and no
 * physical completion claim. Caller records attempt before invoking. */
enum wr_iot_restart_up_result wr_iot_restart_guest_down(void);
/* Output untouched on read failure. Administrative state only. */
int wr_iot_restart_guest_admin_state(int *);
#endif
