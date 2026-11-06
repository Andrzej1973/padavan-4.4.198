#include <assert.h>
#include <stdio.h>
#include "mcu-boot-scheduler-quota.h"
int main(void)
{
 assert(!wr_iot_boot_scheduler_quota_valid(~0U,1,1,1));
 assert(!wr_iot_boot_scheduler_quota_valid(0,1,1,1));
 assert(wr_iot_boot_scheduler_quota_valid(100U<<16,20,10,0));
 assert(!wr_iot_boot_scheduler_quota_valid(30U<<16,20,10,0));
 assert(!wr_iot_boot_scheduler_quota_valid(29U<<16,20,10,0));
 assert(!wr_iot_boot_scheduler_quota_valid(100U<<16,~0U,10,0));
 assert(!wr_iot_boot_scheduler_quota_valid(100U<<16,20,~0U,0));
 assert(wr_iot_boot_scheduler_quota_valid(1U<<16,20,10,1));
 puts("PASS quota bus/zero/boundary/overflow and SDK single-group cases; source arithmetic only");
}
