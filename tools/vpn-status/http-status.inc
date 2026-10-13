#if defined(BOARD_WR1200JS)
#include "wr-vpn/handshake-runtime.h"
#include <time.h>
static struct wr_handshake_runtime wr_vpn_runtime[2];
static int wr_vpn_initialized,wr_vpn_scheduled;
static uint64_t wr_vpn_next;
static void wr_vpn_init(void)
{
 if(!wr_vpn_initialized){
  wr_handshake_runtime_init(&wr_vpn_runtime[0]);
  wr_handshake_runtime_init(&wr_vpn_runtime[1]);wr_vpn_initialized=1;
 }
}
void wr_vpn_background_tick(void)
{
 uint64_t now=(uint64_t)uptime();unsigned i;time_t wall;
 wr_vpn_init();
 for(i=0;i<2;i++)wr_handshake_runtime_tick(&wr_vpn_runtime[i],now);
 if(wr_vpn_scheduled&&now<wr_vpn_next&&wr_vpn_next-now<=30)return;
 wr_vpn_scheduled=1;wr_vpn_next=now+30;wall=time(NULL);
 for(i=0;i<2;i++)if(wr_vpn_runtime[i].pid<=0){
  if(wall<0||!wr_handshake_runtime_start(&wr_vpn_runtime[i],i?"wg1":"wg0",now,(uint64_t)wall))
   wr_handshake_cache_publish(&wr_vpn_runtime[i].cache,now,0,NULL);
 }
}
void wr_vpn_background_close(void)
{
 unsigned i;if(!wr_vpn_initialized)return;
 for(i=0;i<2;i++){
  wr_handshake_runtime_cancel(&wr_vpn_runtime[i]);
  wr_handshake_runtime_tick(&wr_vpn_runtime[i],(uint64_t)uptime());
 }
 /* HTTP process exits immediately afterwards; unreaped killed children are
  * inherited by init. No synchronous wait in request or shutdown paths. */
}
static int ej_wr_vpn_handshake_state(int eid,webs_t wp,int argc,char **argv)
{
 unsigned index;uint64_t age;enum wr_handshake_cache_state state;
 const struct wr_handshake_observation *o;(void)eid;
 if(argc!=1||!argv||!argv[0])return websWrite(wp,"{\"state\":0}");
 if(!strcmp(argv[0],"client"))index=0;
 else if(!strcmp(argv[0],"server"))index=1;
 else return websWrite(wp,"{\"state\":0}");
 wr_vpn_init();
 state=wr_handshake_cache_get(&wr_vpn_runtime[index].cache,(uint64_t)uptime(),60,&age);
 if(state==WR_HS_UNKNOWN)return websWrite(wp,"{\"state\":0}");
 o=&wr_vpn_runtime[index].cache.observation;
 return websWrite(wp,"{\"state\":%d,\"sample_age\":%llu,\"peers\":%u,\"never\":%u,\"recent\":%u,\"old\":%u,\"future\":%u,\"has_age\":%d,\"youngest_age\":%llu}",
  (int)state,(unsigned long long)age,o->peers,o->never,o->recent,o->old,o->future,o->has_age,(unsigned long long)o->youngest_age);
}
#endif
