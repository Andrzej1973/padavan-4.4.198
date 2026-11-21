#ifndef WR_IOT_RADIO_STOP_CONTRACT_H
#define WR_IOT_RADIO_STOP_CONTRACT_H
/* Strong activation-controller boundary, intentionally no fallback backend.
 * Called outside signal context under the RC shutdown admission fence.
 * Controller owns serialization, current transaction and service guard. It
 * returns exactly 1 only after IoT is safely closed and its owned network /
 * service state is recovered. Driver uncertainty, absent ownership, busy
 * recovery or missing RF/DMA proof returns failure and retains isolation.
 * This call must not recursively invoke physical radio stop/restart. Caller
 * performs no separate bridge/gate cleanup and must not equate admin DOWN,
 * diagnostics or configuration-only CLOSED with successful preparation.
 * An implementation is required before linking this prepared RC feature;
 * do not provide a weak or constant-success definition to satisfy the linker.
 */
int wr_iot_activation_prepare_radio_stop(void);
#endif
