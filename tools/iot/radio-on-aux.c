#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include "radio-on-aux.h"
#include "rc-backend.h"
#include "service-guard.h"
static int aux_guard(void)
{int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;}
int wr_iot_on_aux_down_current(void)
{
 static const char *const names[]={"wds3","wds2","wds1","wds0","apcli0"};
 static const char *const masters[]={"/sys/class/net/wds3/master","/sys/class/net/wds2/master","/sys/class/net/wds1/master","/sys/class/net/wds0/master","/sys/class/net/apcli0/master"};
 struct wr_iot_rc_mode mode={0};unsigned i;
 if(!aux_guard()||!wr_iot_rc_mode_read(&mode)||mode.router!=1||mode.radio!=1||mode.mode!=0)return 0;
 for(i=0;i<5;i++){
  struct ifreq r={0};unsigned index;int fd,read_ok,closed;char link;
  errno=0;index=if_nametoindex(names[i]);
  if(!index){
   if(errno!=ENODEV&&errno!=ENXIO)return 0;
   errno=0;if(if_nametoindex(names[i])||(errno!=ENODEV&&errno!=ENXIO))return 0;
   continue;
  }
  fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
  memcpy(r.ifr_name,names[i],strlen(names[i])+1);
  read_ok=ioctl(fd,SIOCGIFFLAGS,&r)==0&&!(r.ifr_flags&IFF_UP);
  closed=close(fd);if(!read_ok||closed)return 0;
  errno=0;if(readlink(masters[i],&link,1)>=0||errno!=ENOENT||if_nametoindex(names[i])!=index)return 0;
 }
 return aux_guard()&&wr_iot_rc_mode_read(&mode)&&mode.router==1&&mode.radio==1&&mode.mode==0;
}
