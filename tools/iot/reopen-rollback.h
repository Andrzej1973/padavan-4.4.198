#ifndef WR_IOT_REOPEN_ROLLBACK_H
#define WR_IOT_REOPEN_ROLLBACK_H
#include "start-network-rollback.h"
#include "reopen-witness.h"
/* Only before a new OPEN can have been submitted. Previous CLOSED witness
 * remains valid; all possible new network/DNS mutations retain provenance. */
int wr_iot_reopen_rollback_step(struct wr_iot_start_network_rollback *,
 struct wr_iot_start_network *,struct wr_iot_start_admission *,
 const struct wr_iot_open_controller *,const struct wr_iot_reopen_witness *);
#endif
