#include <assert.h>
#include <stdio.h>
#include "guest-schedule.h"
int main(void)
{
 char days[8],interval[9];unsigned int mask,i,hour,minute;
 for(mask=0;mask<128;mask++){
  for(i=0;i<7;i++)days[i]=(mask&(1U<<i))?'1':'0';
  days[7]=0;
  assert(wr_modern_guest_schedule_validate(days,"08002200","22000800")==WR_GUEST_SCHEDULE_OK);
 }
 for(hour=0;hour<24;hour++)for(minute=0;minute<60;minute++){
  snprintf(interval,sizeof(interval),"%02u%02u2359",hour,minute);
  assert(wr_modern_guest_schedule_validate("1111111",interval,"00002359")==
    ((hour==23&&minute==59)?WR_GUEST_SCHEDULE_EQUAL:WR_GUEST_SCHEDULE_OK));
 }
 assert(wr_modern_guest_schedule_validate(NULL,"00002359","00002359")==WR_GUEST_SCHEDULE_MISSING);
 assert(wr_modern_guest_schedule_validate("1111111",NULL,"00002359")==WR_GUEST_SCHEDULE_MISSING);
 assert(wr_modern_guest_schedule_validate("1111111","00002359",NULL)==WR_GUEST_SCHEDULE_MISSING);
 const char *bad_days[]={"","111111","11111111","11111x1"," 111111","111111\n"};
 for(i=0;i<sizeof(bad_days)/sizeof(bad_days[0]);i++)assert(wr_modern_guest_schedule_validate(bad_days[i],"00002359","00002359")==WR_GUEST_SCHEDULE_INVALID);
 const char *bad_time[]={"","0000235","000023599","24002359","00602359","00002400","00002360","-1002359","0000x359"," 0002359"};
 for(i=0;i<sizeof(bad_time)/sizeof(bad_time[0]);i++){
  assert(wr_modern_guest_schedule_validate("1111111",bad_time[i],"00002359")==WR_GUEST_SCHEDULE_INVALID);
  assert(wr_modern_guest_schedule_validate("1111111","00002359",bad_time[i])==WR_GUEST_SCHEDULE_INVALID);
 }
 assert(wr_modern_guest_schedule_validate("0000000","08000800","00002359")==WR_GUEST_SCHEDULE_EQUAL);
 assert(wr_modern_guest_schedule_validate("0000000","00002359","08000800")==WR_GUEST_SCHEDULE_EQUAL);
 puts("PASS Guest schedule admission component: day masks, full-day minute bounds, overnight, missing/malformed/equal rejected; not CGI integration");
 return 0;
}
