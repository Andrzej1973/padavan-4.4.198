#define _GNU_SOURCE
#include "roaming-json.h"
#include "action-json.h"
static struct wr_action_log actions;
static char action_output[65536];
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
 {
 size_t action_length;struct wr_action_event e={0};char epoch[65];
 memset(&history,0,sizeof(history));memset(epoch,'"',64);epoch[64]=0;
 for(i=0;i<256;i++)wr_roam_event_add(&history,9007199254740991ULL,"FE:FF:FF:FF:FF:FF",WR_ROAM_BAND_CHANGE,1,2);
 for(i=0;i<256;i++)history.events[i].sequence=9007199254740736ULL+i;
 history.dropped=history.client_dropped=history.client_evictions=4294967295U;
 assert(wr_roam_json(&history,epoch,output,sizeof(output),&n));
 e.session=UINT64_MAX;e.uptime_ms=9007199254740991ULL;e.cookie=4294967295U;
 memset(e.mac,255,6);e.mac[0]=254;e.source=WR_ACTION_STEERING;e.stage=WR_ACTION_IOCTL_ACCEPTED;e.operation=WR_ACTION_REMOVE_CANDIDATE;e.radio=1;e.bss=15;e.result=-2147483647-1;
 actions.count=256;actions.dropped=actions.rejected=actions.session.missing=UINT64_MAX;
 for(i=0;i<256;i++){e.sequence=9007199254740736ULL+i;actions.events[i]=e;}
 assert(wr_action_json(&actions,action_output,sizeof(action_output),&action_length));
 /* Bound metadata added by the HTTP hook, including max uptime and states. */
 assert(n+action_length+256<131072);
 printf("PASS maximum-width 512-event response: %zu bytes plus bounded metadata, browser limit 131072\n",n+action_length);
 }
 puts("PASS chronological roaming JSON, overflow disclosure and bounded failure");return 0;
}
