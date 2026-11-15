#ifndef WR_IOT_RADIO_OFF_OBSERVE_H
#define WR_IOT_RADIO_OFF_OBSERVE_H
#include "physical-stop-wire.h"
/* Fresh Linux-only post-RELEASE QUERY; observation only, not a future lease. */
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request *);
/* Dedicated private resume preflight requires active admission plus retained
 * radio ownership. Query only; no Main UP or receipt consumption. */
int wr_iot_radio_resume_down_observed(const struct wr_iot_physical_stop_request *);
/* Recovery-only readback tolerates pending shutdown; never ON permission.
 * Caller must independently exclude any possible Main UP before restoring. */
int wr_iot_radio_recovery_down_observed(const struct wr_iot_physical_stop_request *);
#endif
