/* Both owners require the same nettask lock. The global lease spans every
 * scheduling call; the data lease additionally excludes non-MCU submissions.
 * Callback completion still requires actual tasklet/work joins. */
#ifndef WR_IOT_NETTASK_LANE_OWNER_H
#define WR_IOT_NETTASK_LANE_OWNER_H
#include "tasklet-schedule-owner.h"
static inline int wr_iot_nettask_lane_enter(
 struct wr_iot_tasklet_schedule_owner *all,
 struct wr_iot_tasklet_schedule_owner *data,int mcu)
{
 if(!wr_iot_tasklet_schedule_enter(all))return 0;
 if(!mcu&&!wr_iot_tasklet_schedule_enter(data)){
  (void)wr_iot_tasklet_schedule_leave(all);return 0;
 }
 return 1;
}
static inline int wr_iot_nettask_lane_leave(
 struct wr_iot_tasklet_schedule_owner *all,
 struct wr_iot_tasklet_schedule_owner *data,int mcu)
{
 int valid=1;
 if(!mcu)valid=wr_iot_tasklet_schedule_leave(data);
 return wr_iot_tasklet_schedule_leave(all)&&valid;
}
#endif
