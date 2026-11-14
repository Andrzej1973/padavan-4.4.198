#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "physical-stop-down.h"
enum wr_iot_physical_down_result wr_iot_physical_stop_down(void)
{
 struct ifreq request={0};int fd,result,closed;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
 if(fd<0)return WR_PHYSICAL_DOWN_NOT_SUBMITTED;
 memcpy(request.ifr_name,"ra0",4);
 if(ioctl(fd,SIOCGIFFLAGS,&request)){
  (void)close(fd);return WR_PHYSICAL_DOWN_NOT_SUBMITTED;
 }
 /* Already DOWN may be a prior failed ndo_stop; never manufacture a result. */
 if(!(request.ifr_flags&IFF_UP)){
  (void)close(fd);return WR_PHYSICAL_DOWN_NOT_SUBMITTED;
 }
 request.ifr_flags&=~IFF_UP;
 result=ioctl(fd,SIOCSIFFLAGS,&request);closed=close(fd);
 /* Linux ignores ndo_stop's return. Even zero requires the separate exact
  * driver completion receipt before any reopen/profile reload. */
 return result||closed?WR_PHYSICAL_DOWN_UNCERTAIN:WR_PHYSICAL_DOWN_IOCTL_RETURNED;
}
