#include "quarantine.h"
#include "quarantine-live.h"
#include "bridge.h"
#include "service-guard.h"
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
static int eligible(int bridge_down){
 struct ifreq request;int guard,fd,down;
 guard=wr_iot_service_guard_dup();if(guard<0)return 0;
 close(guard);
 if(!wr_iot_bridge_is_owned())return 0;
 if(bridge_down){
  fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
  memset(&request,0,sizeof(request));strcpy(request.ifr_name,"br-iot");
  down=ioctl(fd,SIOCGIFFLAGS,&request)==0&&!(request.ifr_flags&IFF_UP);
  close(fd);if(!down)return 0;
 }
 if(if_nametoindex("ra2")){
  fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
  memset(&request,0,sizeof(request));strcpy(request.ifr_name,"ra2");
  down=ioctl(fd,SIOCGIFFLAGS,&request)==0&&!(request.ifr_flags&IFF_UP);
  close(fd);if(!down)return 0;
 }
 return 1;
}
int wr_iot_quarantine_can_apply(void){return eligible(1);}
int wr_iot_quarantine_ready(void){return eligible(0)&&wr_iot_quarantine_live(0)&&wr_iot_quarantine_live(1);}
int wr_iot_policy_rules_ready(const char *ipv4,const char *ipv6){
 return eligible(0)&&wr_iot_policy_live(0,ipv4)&&wr_iot_policy_live(1,ipv6);
}
