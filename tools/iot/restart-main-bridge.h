#ifndef WR_IOT_RESTART_MAIN_BRIDGE_H
#define WR_IOT_RESTART_MAIN_BRIDGE_H
/* Exact pinned WR1200JS ra0 -> br0. Caller holds restart/service ownership.
 * No radio UP/DOWN or arbitrary interface arguments. Mutation outcome is not
 * network/client acceptance; repeated invocation belongs to retained owner. */
enum wr_iot_main_bridge_result {WR_MAIN_BRIDGE_REFUSED,
 WR_MAIN_BRIDGE_UNCERTAIN,WR_MAIN_BRIDGE_ATTACHED};
int wr_iot_restart_main_bridge_current(void);
enum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void);
#endif
