#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <linux/sockios.h>
#include <net/if.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "radio-off-bridge.h"
#include "radio-off-observe.h"
#include "service-guard.h"
static int off_master(const char *name)
{
 char key[96],value[256];ssize_t n;char *last;
 if(snprintf(key,sizeof(key),"/sys/class/net/%s/master",name)>=(int)sizeof(key))return -1;
 n=readlink(key,value,sizeof(value)-1);
 if(n<0)return errno==ENOENT?0:-1;
 if((size_t)n>=sizeof(value)-1)return -1;
 value[n]=0;last=strrchr(value,'/');return last&&!strcmp(last+1,"br0")?1:-1;
}
static enum wr_iot_off_bridge_result off_bridge_check(
 const struct wr_iot_physical_stop_request *released,unsigned slot,int detach,int finalizing)
{
 static const char *const names[]={"ra1","ra0","wds3","wds2","wds1","wds0","apcli0"};
 struct ifreq r={0};struct stat bridge;unsigned index,br;int token,fd,state,result,closed;
 enum wr_iot_off_bridge_result outcome=WR_OFF_BRIDGE_REFUSED;
 int (*observe)(const struct wr_iot_physical_stop_request *)=finalizing?
  wr_iot_radio_recovery_down_observed:wr_iot_radio_off_observed;
 if(slot>=sizeof(names)/sizeof(names[0])||(finalizing&&detach))return outcome;
 token=wr_iot_service_guard_enter(1);if(token!=1)return outcome;
 if(!observe(released))goto done;
 errno=0;index=if_nametoindex(names[slot]);
 if(!index){
  if(slot!=1&&(errno==ENODEV||errno==ENXIO)&&observe(released))outcome=WR_OFF_BRIDGE_DETACHED;
  goto done;
 }
 br=if_nametoindex("br0");
 if(!br||br==index||stat("/sys/class/net/br0/bridge",&bridge)||!S_ISDIR(bridge.st_mode))goto done;
 state=off_master(names[slot]);if(state<0)goto done;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)goto done;
 snprintf(r.ifr_name,sizeof(r.ifr_name),"%s",names[slot]);
 if(ioctl(fd,SIOCGIFFLAGS,&r)||(r.ifr_flags&IFF_UP)||
    if_nametoindex(names[slot])!=index||if_nametoindex("br0")!=br||
    off_master(names[slot])!=state||!observe(released)){
  (void)close(fd);goto done;
 }
 if(!state){
  closed=close(fd);
  if(!closed&&off_master(names[slot])==0&&if_nametoindex(names[slot])==index&&
     observe(released))outcome=WR_OFF_BRIDGE_DETACHED;
  goto done;
 }
 if(!detach){(void)close(fd);goto done;}
 memset(&r,0,sizeof(r));memcpy(r.ifr_name,"br0",4);r.ifr_ifindex=(int)index;
 result=ioctl(fd,SIOCBRDELIF,&r);closed=close(fd);
 outcome=WR_OFF_BRIDGE_UNCERTAIN;
 if(!result&&!closed&&off_master(names[slot])==0&&if_nametoindex(names[slot])==index&&
    if_nametoindex("br0")==br&&observe(released))outcome=WR_OFF_BRIDGE_DETACHED;
 done:wr_iot_service_guard_leave(token);return outcome;
}

enum wr_iot_off_bridge_result wr_iot_radio_off_bridge_detach(
 const struct wr_iot_physical_stop_request *released,unsigned slot)
{return off_bridge_check(released,slot,1,0);}
int wr_iot_radio_off_bridge_observed(const struct wr_iot_physical_stop_request *released,unsigned slot)
{return off_bridge_check(released,slot,0,0)==WR_OFF_BRIDGE_DETACHED;}

int wr_iot_radio_off_bridge_final_observed(const struct wr_iot_physical_stop_request *released,unsigned slot)
{return off_bridge_check(released,slot,0,1)==WR_OFF_BRIDGE_DETACHED;}
