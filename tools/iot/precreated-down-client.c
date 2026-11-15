#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include "precreated-down-client.h"
int wr_iot_driver_initial_down_read(const unsigned char *nonce,struct wr_iot_down_result *out)
{
 struct ifreq request={0};unsigned char wire[64]={0};int fd,result,closed;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!wr_iot_down_query_encode(wire,sizeof(wire),nonce))return 0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);closed=close(fd);
 if(result||closed)return 0;
 return wr_iot_down_reply_decode(out,nonce,wire,sizeof(wire));
}
