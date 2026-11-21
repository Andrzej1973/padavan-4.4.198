#include "tasklet-schedule-owner.h"
#include <assert.h>
int main(void){struct wr_iot_tasklet_schedule_owner s;
 wr_iot_tasklet_schedule_init(&s);assert(!wr_iot_tasklet_schedule_enter(&s));
 assert(!wr_iot_tasklet_schedule_open(&s,0,1));assert(!wr_iot_tasklet_schedule_open(&s,1,0));
 assert(wr_iot_tasklet_schedule_open(&s,1,1));
 assert(wr_iot_tasklet_schedule_enter(&s)); /* Producer admitted, not yet submitted. */
 wr_iot_tasklet_schedule_block(&s);
 assert(!wr_iot_tasklet_schedule_enter(&s)&&!wr_iot_tasklet_schedule_may_join(&s));
 assert(!wr_iot_tasklet_schedule_open(&s,1,1));
 assert(wr_iot_tasklet_schedule_leave(&s)); /* Submit completed after fence. */
 assert(wr_iot_tasklet_schedule_may_join(&s));
 assert(!wr_iot_tasklet_schedule_enter(&s));
 assert(wr_iot_tasklet_schedule_open(&s,1,1));
 assert(wr_iot_tasklet_schedule_enter(&s)&&wr_iot_tasklet_schedule_enter(&s));
 wr_iot_tasklet_schedule_block(&s);assert(wr_iot_tasklet_schedule_leave(&s));
 assert(!wr_iot_tasklet_schedule_may_join(&s));assert(wr_iot_tasklet_schedule_leave(&s));
 assert(wr_iot_tasklet_schedule_may_join(&s));
 assert(!wr_iot_tasklet_schedule_leave(&s)&&s.poisoned);
 assert(!wr_iot_tasklet_schedule_may_join(&s)&&!wr_iot_tasklet_schedule_open(&s,1,1));
 wr_iot_tasklet_schedule_init(&s);assert(wr_iot_tasklet_schedule_open(&s,1,1));
 s.inflight=~0U;assert(!wr_iot_tasklet_schedule_enter(&s)&&s.blocked&&s.poisoned);
 return 0;
}
