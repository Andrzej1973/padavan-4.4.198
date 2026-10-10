#define _GNU_SOURCE
#include "roaming-json.h"
#include <assert.h>
static struct wr_roam_history history;
static char output[65536];
int main(void){size_t n;unsigned int i;
 assert(wr_roam_json(&history,"session",output,sizeof(output),&n)&&n);
 assert(strstr(output,"\"events\":[]"));
 for(i=0;i<260;i++)wr_roam_event_add(&history,i*5000,NULL,WR_ROAM_GAP,0,0);
 assert(wr_roam_json(&history,"session",output,sizeof(output),&n));
 assert(strstr(output,"\"dropped\":4")&&strstr(output,"\"sequence\":5,"));
 assert(!strstr(output,"\"sequence\":1,"));
 assert(!wr_roam_json(&history,"session",output,20,&n)&&n==0);
 history.events[history.next].kind=99;
 assert(!wr_roam_json(&history,"session",output,sizeof(output),&n)&&n==0);
 puts("PASS chronological roaming JSON, overflow disclosure and bounded failure");return 0;
}
