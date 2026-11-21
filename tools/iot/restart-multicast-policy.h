#ifndef WR_IOT_RESTART_MULTICAST_POLICY_H
#define WR_IOT_RESTART_MULTICAST_POLICY_H
struct wr_iot_multicast_policy {int required,enabled,guest;};
/* Mode0 SDK policy under service guard. required=0 with USE_IGMP_SNOOP;
 * otherwise preserve boolean normalization of saved IgmpSnEnable. */
int wr_iot_rc_restart_multicast_policy(struct wr_iot_multicast_policy *);
#endif
