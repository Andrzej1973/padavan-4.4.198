#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "physical-rebind-client.h"
enum wr_iot_rebind_call_result wr_iot_physical_rebind_call(
 const struct wr_iot_physical_rebind_request *input)
{
 unsigned char wire[WR_REBIND_OPEN_BYTES]={0};volatile unsigned char *wipe=wire;
 struct ifreq request={0};unsigned length,i;int fd,result,closed;
 enum wr_iot_rebind_call_result outcome=WR_REBIND_NOT_SUBMITTED;
 if(!input)return outcome;
 length=input->operation==WR_REBIND_OBSERVE?WR_REBIND_OBSERVE_BYTES:WR_REBIND_OPEN_BYTES;
 if(!wr_iot_physical_rebind_encode(wire,length,input))goto done;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)goto done;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);closed=close(fd);
 outcome=result||closed?WR_REBIND_UNCERTAIN:WR_REBIND_IOCTL_RETURNED;
 done:for(i=0;i<sizeof(wire);i++)wipe[i]=0;
 return outcome;
}
