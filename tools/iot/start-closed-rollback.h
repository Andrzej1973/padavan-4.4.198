/* Startup rollback after explicit CLOSE-owner release, before DNS commit.
 * Retain the original startup snapshot and network attempt history throughout.
 * Serial caller must prohibit DNS commit/new OPEN; no RF acceptance implied. */
#ifndef WR_IOT_START_CLOSED_ROLLBACK_H
#define WR_IOT_START_CLOSED_ROLLBACK_H
#include "start-close.h"
#include "start-network-rollback.h"
int wr_iot_start_closed_rollback_step(struct wr_iot_start_network_rollback *,
 struct wr_iot_start_network *,struct wr_iot_start_admission *,
 const struct wr_iot_open_controller *,struct wr_iot_start_close *);
#endif
