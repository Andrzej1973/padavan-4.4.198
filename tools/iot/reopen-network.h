#ifndef WR_IOT_REOPEN_NETWORK_H
#define WR_IOT_REOPEN_NETWORK_H
#include "start-network.h"
#include "reopen-witness.h"
/* Same seven operations/order as initial network startup, but only a copied
 * post-CLOSE witness may authorize each step. No initial-idle substitution. */
int wr_iot_reopen_network_step(struct wr_iot_start_network *,
 struct wr_iot_start_admission *,const struct wr_iot_request *,
 const struct wr_iot_reopen_witness *);
#endif
