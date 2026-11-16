#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <signal.h>
#include "initial-shutdown-owner.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static unsigned stock;
static void handler(int sig){if(!wr_iot_rc_shutdown_note(sig))stock++;}
int main(void){
 struct sigaction a={0};struct wr_iot_radio_stop_fence fence={0};
 struct wr_iot_initial_shutdown_owner s={0},bad;
 a.sa_handler=handler;sigemptyset(&a.sa_mask);
 assert(!sigaction(SIGTERM,&a,0)&&!sigaction(SIGQUIT,&a,0));
 assert(!wr_iot_initial_shutdown_claim(&s,&fence));
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(wr_iot_radio_stop_fence_begin_routed_shutdown(&fence));
 assert(wr_iot_initial_shutdown_claim(&s,&fence));
 assert(wr_iot_initial_shutdown_current(&s)&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(!wr_iot_initial_shutdown_claim(&s,&fence));
 for(unsigned fault=0;fault<7;fault++){
  struct wr_iot_rc_shutdown_admission old=wr_iot_rc_shutdown;
  struct wr_iot_radio_stop_fence oldf=fence;bad=s;
  switch(fault){case 0:bad.owner++;break;case 1:bad.signal=SIGQUIT;break;
   case 2:fence.level=2;break;case 3:wr_iot_rc_shutdown.pending=SIGQUIT;break;
   case 4:wr_iot_rc_shutdown.radio_on_owned=1;break;
   case 5:wr_iot_rc_shutdown.replay_signal=SIGTERM;break;
   case 6:wr_iot_rc_shutdown.normal_route_armed=0;break;}
  assert(!wr_iot_initial_shutdown_current(&bad));
  wr_iot_rc_shutdown=old;fence=oldf;
 }
 assert(!raise(SIGQUIT)); /* blocked duplicate may not replace original */
 assert(wr_iot_initial_shutdown_current(&s)&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(wr_iot_radio_stop_fence_end(&fence));
 assert(!wr_iot_initial_shutdown_current(&s)&&!stock);
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 return 0;
}
