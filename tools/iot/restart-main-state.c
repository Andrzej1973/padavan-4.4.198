#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "restart-main-state.h"
int wr_iot_restart_main_down(void)
{
 struct ifreq request={0};int fd,read_result,close_result;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra0",4);
 read_result=ioctl(fd,SIOCGIFFLAGS,&request);close_result=close(fd);
 return !read_result&&!close_result&&!(request.ifr_flags&IFF_UP);
}
