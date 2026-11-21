#include "mbss-reaper-gate.h"
#include <assert.h>
int main(void){struct wr_iot_mbss_reaper_gate g;
 wr_iot_mbss_reaper_gate_init(&g);assert(wr_iot_mbss_reaper_idle(&g));
 assert(wr_iot_mbss_submission_enter(&g));assert(!wr_iot_mbss_reaper_enter(&g));
 wr_iot_mbss_reaper_stop(&g);assert(!wr_iot_mbss_submission_enter(&g));
 assert(wr_iot_mbss_submission_leave(&g));assert(wr_iot_mbss_reaper_enter(&g));
 assert(!wr_iot_mbss_reaper_enter(&g)&&!wr_iot_mbss_submission_enter(&g));
 assert(!wr_iot_mbss_reaper_idle(&g));assert(wr_iot_mbss_reaper_leave(&g));
 assert(g.stopped&&wr_iot_mbss_reaper_idle(&g)&&!wr_iot_mbss_submission_enter(&g));
 assert(wr_iot_mbss_reaper_enter(&g)&&wr_iot_mbss_reaper_leave(&g));
 wr_iot_mbss_reaper_gate_init(&g);assert(wr_iot_mbss_reaper_enter(&g));
 assert(!wr_iot_mbss_submission_enter(&g));assert(wr_iot_mbss_reaper_leave(&g));
 assert(wr_iot_mbss_submission_enter(&g)&&wr_iot_mbss_submission_leave(&g));
 assert(!wr_iot_mbss_submission_leave(&g)&&g.poisoned&&!wr_iot_mbss_reaper_idle(&g));
 assert(!wr_iot_mbss_reaper_enter(&g)&&!wr_iot_mbss_submission_enter(&g));
 wr_iot_mbss_reaper_gate_init(&g);g.submissions=~0U;
 assert(!wr_iot_mbss_submission_enter(&g)&&g.poisoned);
 wr_iot_mbss_reaper_gate_init(&g);assert(!wr_iot_mbss_reaper_leave(&g)&&g.poisoned);
 return 0;
}
