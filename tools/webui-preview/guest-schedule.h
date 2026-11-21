/* Modern Guest request component. No NVRAM, clock, service or driver access.
 * Classic accepts overnight intervals but rejects equal start/end times.
 * Empty day selection is valid (Guest never scheduled); malformed is not empty.
 */
#ifndef WR_MODERN_GUEST_SCHEDULE_H
#define WR_MODERN_GUEST_SCHEDULE_H
#include <string.h>
enum wr_modern_guest_schedule_result {
 WR_GUEST_SCHEDULE_OK, WR_GUEST_SCHEDULE_MISSING,
 WR_GUEST_SCHEDULE_INVALID, WR_GUEST_SCHEDULE_EQUAL
};
static enum wr_modern_guest_schedule_result wr_modern_guest_interval(const char *value)
{
 unsigned int i;
 if(!value)return WR_GUEST_SCHEDULE_MISSING;
 if(strlen(value)!=8)return WR_GUEST_SCHEDULE_INVALID;
 for(i=0;i<8;i++)if(value[i]<'0'||value[i]>'9')return WR_GUEST_SCHEDULE_INVALID;
 if(value[0]>'2'||(value[0]=='2'&&value[1]>'3')||value[2]>'5'||
    value[4]>'2'||(value[4]=='2'&&value[5]>'3')||value[6]>'5')return WR_GUEST_SCHEDULE_INVALID;
 return memcmp(value,value+4,4)?WR_GUEST_SCHEDULE_OK:WR_GUEST_SCHEDULE_EQUAL;
}
static enum wr_modern_guest_schedule_result wr_modern_guest_schedule_validate(
 const char *days,const char *weekday,const char *weekend)
{
 unsigned int i;
 enum wr_modern_guest_schedule_result result;
 if(!days||!weekday||!weekend)return WR_GUEST_SCHEDULE_MISSING;
 if(strlen(days)!=7)return WR_GUEST_SCHEDULE_INVALID;
 for(i=0;i<7;i++)if(days[i]!='0'&&days[i]!='1')return WR_GUEST_SCHEDULE_INVALID;
 result=wr_modern_guest_interval(weekday);
 if(result!=WR_GUEST_SCHEDULE_OK)return result;
 return wr_modern_guest_interval(weekend);
}
#endif
