#ifndef WR_IOT_QUARANTINE_H
#define WR_IOT_QUARANTINE_H
/* Read-only, held service guard, owned bridge and administratively down BSS.
 * Kernel IPv4/IPv6 quarantine does not prove vendor HNAT bypass is disabled. */
int wr_iot_quarantine_ready(void);
/* Also requires bridge DOWN; does not mutate kernel state. */
int wr_iot_quarantine_can_apply(void);
/* Installed in firewall_ex.c. Caller retains service guard throughout. */
int wr_iot_quarantine_apply(void);
#endif
