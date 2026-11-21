#ifndef WR_IOT_BOOT_SCHEDULER_QUOTA_H
#define WR_IOT_BOOT_SCHEDULER_QUOTA_H
/* Validate the SDK group0 subtraction without unsigned wraparound.
 * Caller derives reservation counts from exact build/board settings. */
static inline int wr_iot_boot_scheduler_quota_valid(unsigned int raw,
 unsigned int beacon_pages,unsigned int command_pages,int single_group)
{
 unsigned int pages;
 if(raw==~0U)return 0;
 pages=(raw>>16)&0xfffU;
 if(!pages)return 0;
 if(single_group)return 1;
 if(beacon_pages>pages)return 0;
 return command_pages<pages-beacon_pages;
}
#endif
