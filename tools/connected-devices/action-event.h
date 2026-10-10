#ifndef WR_ACTION_EVENT_H
#define WR_ACTION_EVENT_H
#include <stdint.h>
#include <stddef.h>
/* Local action evidence, distinct from association history. Transport must
 * authenticate the producer; this validator cannot prove producer identity. */
enum wr_action_source {WR_ACTION_STEERING=1,WR_ACTION_RSSI};
enum wr_action_stage {WR_ACTION_INTENT=1,WR_ACTION_IOCTL_ACCEPTED,WR_ACTION_IOCTL_FAILED,WR_ACTION_DRIVER_ACK,WR_ACTION_ALLOC_FAILED,WR_ACTION_FRAME_SUBMITTED,WR_ACTION_ENTRY_REMOVED};
struct wr_action_event {uint64_t session,sequence,uptime_ms;uint32_t cookie;unsigned char mac[6],source,stage,radio,bss;int result;};
static inline int wr_action_valid(const struct wr_action_event *e){
 unsigned int i;int any=0;
 if(!e||!e->session||!e->sequence||e->sequence>9007199254740991ULL||e->uptime_ms>9007199254740991ULL||e->radio>1||e->bss>15||(e->mac[0]&1))return 0;
 for(i=0;i<6;i++){any|=e->mac[i];}
 if(!any)return 0;
 if(e->source==WR_ACTION_STEERING){
  if(e->stage<WR_ACTION_INTENT||e->stage>WR_ACTION_DRIVER_ACK)return 0;
 }else if(e->source==WR_ACTION_RSSI){
  if(e->stage!=WR_ACTION_INTENT&&e->stage!=WR_ACTION_ALLOC_FAILED&&e->stage!=WR_ACTION_FRAME_SUBMITTED&&e->stage!=WR_ACTION_ENTRY_REMOVED)return 0;
 }else return 0;
 /* A queued frame or removed local entry never proves a destination roam. */
 return 1;
}
#endif
