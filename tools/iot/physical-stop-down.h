/* Fixed main-interface DOWN in the calling RC task. Not teardown acceptance.
 * Caller holds shutdown/service admission and retains its exact stop attempt.
 * No shell, retries, UP operation or arbitrary interface argument. */
#ifndef WR_IOT_PHYSICAL_STOP_DOWN_H
#define WR_IOT_PHYSICAL_STOP_DOWN_H
enum wr_iot_physical_down_result {
 WR_PHYSICAL_DOWN_NOT_SUBMITTED,WR_PHYSICAL_DOWN_UNCERTAIN,
 WR_PHYSICAL_DOWN_IOCTL_RETURNED
};
enum wr_iot_physical_down_result wr_iot_physical_stop_down(void);
#endif
