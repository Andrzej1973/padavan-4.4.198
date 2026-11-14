#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "restart-guest-up.h"
enum wr_iot_restart_up_result wr_iot_restart_guest_up(void)
{
 struct ifreq request={0};int fd,result,closed;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
 if(fd<0)return WR_RESTART_UP_NOT_SUBMITTED;
 /* Guest may be opened only while the physical Main is administratively
  * UP. The outer controller separately checks its exact driver epoch. */
 memcpy(request.ifr_name,"ra0",4);
 if(ioctl(fd,SIOCGIFFLAGS,&request)||!(request.ifr_flags&IFF_UP)){
  (void)close(fd);return WR_RESTART_UP_NOT_SUBMITTED;
 }
 memset(&request,0,sizeof(request));memcpy(request.ifr_name,"ra1",4);
 if(ioctl(fd,SIOCGIFFLAGS,&request)){
  (void)close(fd);return WR_RESTART_UP_NOT_SUBMITTED;
 }
 /* A previous/foreign UP is not permission to open twice or claim ownership. */
 if(request.ifr_flags&IFF_UP){(void)close(fd);return WR_RESTART_UP_NOT_SUBMITTED;}
 request.ifr_flags|=IFF_UP;
 result=ioctl(fd,SIOCSIFFLAGS,&request);closed=close(fd);
 return result||closed?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED;
}
/* Read-only administrative observation, never per-BSS firmware readiness. */
int wr_iot_restart_guest_admin_state(int *out)
{
 struct ifreq r={0};int fd,result,closed;
 if(!out)return 0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(r.ifr_name,"ra1",4);result=ioctl(fd,SIOCGIFFLAGS,&r);closed=close(fd);
 if(result||closed)return 0;
 *out=!!(r.ifr_flags&IFF_UP);return 1;
}

/* Fixed Guest administrative shutdown. Never infer DMA/TxS retirement from
 * ioctl return; caller retains recovery ownership and observes DOWN again. */
enum wr_iot_restart_up_result wr_iot_restart_guest_down(void)
{
 struct ifreq r={0};int fd,result,closed;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
 if(fd<0)return WR_RESTART_UP_NOT_SUBMITTED;
 memcpy(r.ifr_name,"ra1",4);
 if(ioctl(fd,SIOCGIFFLAGS,&r)){
  (void)close(fd);return WR_RESTART_UP_NOT_SUBMITTED;
 }
 if(!(r.ifr_flags&IFF_UP)){
  closed=close(fd);
  return closed?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED;
 }
 r.ifr_flags&=~IFF_UP;
 result=ioctl(fd,SIOCSIFFLAGS,&r);closed=close(fd);
 return result||closed?WR_RESTART_UP_UNCERTAIN:WR_RESTART_UP_RETURNED;
}
