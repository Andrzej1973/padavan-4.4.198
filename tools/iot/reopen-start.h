#ifndef WR_IOT_REOPEN_START_H
#define WR_IOT_REOPEN_START_H
#include "start-admission.h"
#include "reopen-witness.h"
/* New startup capture from a copied post-CLOSE witness. The caller retains
 * witness and prior stopped runner separately. No mutation or OPEN here. */
int wr_iot_reopen_start_begin(struct wr_iot_start_admission *,
 const struct wr_iot_reopen_witness *);
/* Stage once; any attempted mutation retains snapshot on failure. */
int wr_iot_reopen_start_stage(struct wr_iot_start_admission *,
 const struct wr_iot_reopen_witness *,const char *(*)(void *,const char *),
 void *,int,int,int);
#endif
