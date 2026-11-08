#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include "driver-api-client.h"
int wr_iot_driver_identity_read(struct wr_iot_driver_identity *out)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_IDENTITY_BYTES]={0};
 int fd,result,closed;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_IDENTITY,&request);
 closed=close(fd);
 if(result||closed)return 0;
 return wr_iot_driver_identity_decode(out,wire,sizeof(wire));
}
enum wr_iot_driver_submit_result wr_iot_driver_open_submit(
 const struct wr_iot_driver_open_request *input)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_OPEN_BYTES]={0};
 volatile unsigned char *wipe=wire;unsigned int i;
 int fd,result,closed;enum wr_iot_driver_submit_result outcome=WR_IOT_DRIVER_NOT_SUBMITTED;
 if(!wr_iot_driver_open_encode(wire,sizeof(wire),input))goto done;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)goto done;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_OPEN,&request);
 closed=close(fd);
 outcome=(result||closed)?WR_IOT_DRIVER_OPEN_UNCERTAIN:WR_IOT_DRIVER_OPEN_COMPLETED;
done:
 for(i=0;i<sizeof(wire);i++)wipe[i]=0;
 return outcome;
}
