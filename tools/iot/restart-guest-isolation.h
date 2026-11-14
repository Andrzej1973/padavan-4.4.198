#ifndef WR_IOT_RESTART_GUEST_ISOLATION_H
#define WR_IOT_RESTART_GUEST_ISOLATION_H
/* Caller owns restart guard and captured policy. Only ra1 DOWN/master br0;
 * write/read vendor bridge isolate_mode. Does not prove routed firewall. */
int wr_iot_restart_guest_isolation_prepare(int);
/* Read-only post-UP parameter check; membership checked by caller. */
int wr_iot_restart_guest_isolation_current(int);
#endif
