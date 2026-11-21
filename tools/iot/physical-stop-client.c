#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include "physical-stop-client.h"
enum wr_iot_physical_call_result wr_iot_physical_stop_call(
 const struct wr_iot_physical_stop_request *input,struct wr_iot_physical_stop_response *out)
{
 struct wr_iot_physical_stop_request retained;
 struct wr_iot_physical_stop_response observed={0};
 struct ifreq request={0};unsigned char wire[64]={0};int fd,result,closed;
 if(!out)return WR_PHYSICAL_CALL_NOT_SUBMITTED;
 /* Input can point into out->identity; preserve it before clearing output. */
 if(input)retained=*input;
 memset(out,0,sizeof(*out));
 if(!input||!wr_iot_physical_stop_request_encode(wire,sizeof(wire),&retained))
  return WR_PHYSICAL_CALL_NOT_SUBMITTED;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
 if(fd<0)return WR_PHYSICAL_CALL_NOT_SUBMITTED;
 memcpy(request.ifr_name,"ra0",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);
 closed=close(fd);
 if(result||closed||!wr_iot_physical_stop_response_decode(&observed,wire,sizeof(wire),&retained))
  return WR_PHYSICAL_CALL_UNCERTAIN;
 *out=observed;return WR_PHYSICAL_CALL_ACKNOWLEDGED;
}
