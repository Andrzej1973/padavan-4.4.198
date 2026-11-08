#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include "driver-api-client.h"
int wr_iot_driver_identity_read(struct wr_iot_driver_identity *out,const unsigned char *id)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_IDENTITY_BYTES]={0};
 int fd,result,closed;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=0;
 if(!wr_iot_driver_query_encode(wire,sizeof(wire),id))return 0;
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
enum wr_iot_driver_submit_result wr_iot_driver_open_requested(
 const char *id,const struct wr_iot_request *input)
{
 struct wr_iot_driver_open_request request={0};struct wr_iot_driver_identity identity;
 struct wr_shared_wifi_fields fields;
 enum wr_iot_driver_submit_result result=WR_IOT_DRIVER_NOT_SUBMITTED;
 unsigned int i,nonzero=0;size_t ssid_length,password_length;
 if(!input||input->enabled!=1||!id||strnlen(id,33)!=32||
    !memchr(input->ssid,0,sizeof(input->ssid))||
    !memchr(input->password,0,sizeof(input->password)))goto done;
 fields.ssid=input->ssid;fields.password=input->password;fields.auth="psk";
 fields.wep="0";fields.wpa_mode="2";fields.crypto="aes";
 if(wr_shared_wifi_validate(&fields)!=WR_SHARED_WIFI_OK)goto done;
 for(i=0;i<32;i++){
  unsigned int nibble;unsigned char c=(unsigned char)id[i];
  if(c>='0'&&c<='9')nibble=c-'0';
  else if(c>='a'&&c<='f')nibble=c-'a'+10;
  else goto done;
  request.request_id[i/2]=(unsigned char)((request.request_id[i/2]<<4)|nibble);
  nonzero|=nibble;
 }
 if(!nonzero)goto done;
 ssid_length=strlen(input->ssid);password_length=strlen(input->password);
 memcpy(request.ssid,input->ssid,ssid_length);
 memcpy(request.password,input->password,password_length);
 request.ssid_length=(unsigned int)ssid_length;request.password_length=(unsigned int)password_length;
 if(!wr_iot_driver_identity_read(&identity,request.request_id))goto done;
 request.adapter_epoch=identity.adapter_epoch;request.device_generation=identity.device_generation;
 result=wr_iot_driver_open_submit(&request);
done:
 wr_iot_driver_request_wipe(&request);return result;
}
int wr_iot_driver_closed_configuration_read(const unsigned char *on_id,
 struct wr_iot_driver_closed_result *out)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_CLOSED_BYTES]={0};
 int fd,result,closed;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=out->open_token=out->close_serial=0;
 if(!wr_iot_driver_closed_query_encode(wire,sizeof(wire),on_id))return 0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);
 closed=close(fd);
 if(result||closed)return 0;
 return wr_iot_driver_closed_decode(out,on_id,wire,sizeof(wire));
}

int wr_iot_driver_refusal_read(const unsigned char *id,struct wr_iot_driver_refusal_result *out)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_CLOSED_BYTES]={0};
 int fd,result,closed;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=out->attempt_token=0;
 if(!wr_iot_driver_refusal_query_encode(wire,sizeof(wire),id))return 0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);closed=close(fd);
 if(result||closed)return 0;
 return wr_iot_driver_refusal_decode(out,id,wire,sizeof(wire));
}
