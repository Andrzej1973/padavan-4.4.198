#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "restart-main-up.h"
enum wr_iot_restart_up_result wr_iot_restart_main_up(void)
{
 struct ifreq request={0};int fd,result,closed;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
 if(fd<0)return WR_RESTART_UP_NOT_SUBMITTED;
 memcpy(request.ifr_name,"ra0",4);
 if(ioctl(fd,SIOCGIFFLAGS,&request)){
  (void)close(fd);return WR_RESTART_UP_NOT_SUBMITTED;
 }
 /* A previous/foreign UP is not permission to open twice or claim ownership. */
 if(request.ifr_flags&IFF_UP){(void)close(fd);return WR_RESTART_UP_NOT_SUBMITTED;}
 request.ifr_flags|=IFF_UP;
 result=ioctl(fd,SIOCSIFFLAGS,&request);closed=close(fd);
 return result||closed?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED;
}
