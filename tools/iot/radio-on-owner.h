#ifndef WR_IOT_RADIO_ON_OWNER_H
#define WR_IOT_RADIO_ON_OWNER_H
struct wr_iot_control_request;
/* Private process-context entry, no stock/UI binding. Return1 means owned,
 * including a retained refusal after fence acquisition; never means ON ready. */
int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request *,int reload);
int wr_iot_radio_on_pending(void);
/* One child phase per call.1 terminal software DONE, still owned;
 * -1 verified pre-UP cancellation already released/wiped the root. */
int wr_iot_radio_on_step(void);
/* Fresh completion/resource proof before wiping private root and exclusion. */
int wr_iot_radio_on_retire(void);
/* Read-only OFF handoff preflight for a released tail. Does not retire the
 * root, clear exclusion, validate the live backend, or authorize Main DOWN. */
int wr_iot_radio_on_off_ready(void);
struct wr_iot_radio_stop_fence;
/* Physical pure-OFF owner only: held fence and guard, after entropy succeeds.
 * Drops inert ON bookkeeping, never closes backend or declares ON success. */
int wr_iot_radio_on_off_handoff(const struct wr_iot_radio_stop_fence *);
#endif
