#ifndef WR_IOT_RESTART_GUEST_POLICY_H
#define WR_IOT_RESTART_GUEST_POLICY_H
/* Read-only SDK policy under caller's service guard. Output unchanged on
 * refusal.1 means stable supported AP/radio/Guest schedule observation only;
 * never implies ra1 existence, UP, bridge membership or isolation readiness. */
int wr_iot_rc_restart_guest_policy(int *);
int wr_iot_rc_restart_guest_isolation_policy(int *);
#endif
