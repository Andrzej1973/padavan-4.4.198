#ifndef WR_IOT_QUARANTINE_H
#define WR_IOT_QUARANTINE_H
/* Read-only, held service guard, owned bridge and administratively down BSS.
 * Kernel IPv4/IPv6 quarantine does not prove vendor HNAT bypass is disabled. */
int wr_iot_quarantine_ready(void);
/* Also requires bridge DOWN; does not mutate kernel state. */
int wr_iot_quarantine_can_apply(void);
/* Installed in firewall_ex.c. Caller retains service guard throughout. */
int wr_iot_quarantine_apply(void);
/* Trusted expected rules only; holds guard, owned bridge, BSS still DOWN. */
int wr_iot_policy_rules_ready(const char *ipv4,const char *ipv6);
/* Rebuild expected policy from current configuration and live inventory. */
int wr_iot_active_filter_ready(const char *lan,const char *wan);
int wr_iot_policy_can_apply(void);
/* Caller has staged enabled gates; does not open the BSS or release snapshots. */
int wr_iot_active_filter_apply(const char *lan,const char *wan);
/* Uses the same WAN selection as start_firewall_ex, refuses changes mid-apply. */
int wr_iot_active_filter_apply_current(void);
#endif
