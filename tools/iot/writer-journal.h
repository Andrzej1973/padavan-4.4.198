#ifndef WR_IOT_WRITER_JOURNAL_H
#define WR_IOT_WRITER_JOURNAL_H
#include "service-transaction.h"
/* Bind only while the caller owns the outer service guard. RC is single threaded.
 * No controller currently activates this binding. Unbound calls preserve legacy behavior. */
int wr_iot_writer_journal_bind(struct wr_iot_service_transaction *transaction);
int wr_iot_writer_journal_unbind(struct wr_iot_service_transaction *transaction);
int wr_iot_writer_journal_begin(unsigned int mask);
int wr_iot_writer_journal_end(unsigned int mask);
int wr_iot_writer_journal_failed(void);
#endif
