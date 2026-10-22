/* Internal candidate envelope only; never accept a userspace pointer here. */
#ifndef WR_IOT_QUEUED_CLEANUP_H
#define WR_IOT_QUEUED_CLEANUP_H
#include "queued-result.h"
#define WR_IOT_CMD_QUEUED_RADIO 0x0D73F001U
struct wr_iot_queue_envelope {struct wr_iot_queued_result *result;};
/* Called before the existing generic buffer free. Queue owns one result ref.
 * May run under CmdQLock: no sleeping, no queue lock acquired from result lock.
 */
static inline void wr_iot_queue_cleanup(PCmdQElmt cmd)
{
 struct wr_iot_queue_envelope *e;
 struct wr_iot_queued_result *r;
 if(cmd->command!=WR_IOT_CMD_QUEUED_RADIO||cmd->CmdFromNdis||
    !cmd->buffer||cmd->bufferlength!=sizeof(*e))return;
 e=(struct wr_iot_queue_envelope *)cmd->buffer;
 r=e->result;e->result=NULL;
 if(!r)return;
 wr_iot_result_cancel(r);
 wr_iot_result_put(r);
}
#endif
