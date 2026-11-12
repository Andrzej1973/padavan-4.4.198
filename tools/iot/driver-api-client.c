#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
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
 struct wr_iot_driver_attempt attempt={0};
 struct wr_iot_driver_open_current_result observed;
 int fd,result,closed;enum wr_iot_driver_submit_result outcome=WR_IOT_DRIVER_NOT_SUBMITTED;
 if(!wr_iot_driver_open_encode(wire,sizeof(wire),input))goto done;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)goto done;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_OPEN,&request);
 closed=close(fd);
 outcome=(result||closed)?WR_IOT_DRIVER_OPEN_UNCERTAIN:WR_IOT_DRIVER_OPEN_COMPLETED;
 if(outcome==WR_IOT_DRIVER_OPEN_COMPLETED){
  attempt.identity.adapter_epoch=input->adapter_epoch;
  attempt.identity.device_generation=input->device_generation;
  memcpy(attempt.request_id,input->request_id,sizeof(attempt.request_id));
  if(!wr_iot_driver_open_current_read(&attempt,&observed))
   outcome=WR_IOT_DRIVER_OPEN_UNCERTAIN;
 }
done:
 for(i=0;i<sizeof(wire);i++)wipe[i]=0;
 return outcome;
}
enum wr_iot_driver_submit_result wr_iot_driver_open_requested_tracked(
 const char *id,const struct wr_iot_request *input,struct wr_iot_driver_attempt *attempt)
{
 struct wr_iot_driver_open_request request={0};struct wr_iot_driver_identity identity;
 struct wr_shared_wifi_fields fields;
 enum wr_iot_driver_submit_result result=WR_IOT_DRIVER_NOT_SUBMITTED;
 unsigned int i,nonzero=0;size_t ssid_length,password_length;
 if(!attempt)return WR_IOT_DRIVER_NOT_SUBMITTED;
 memset(attempt,0,sizeof(*attempt));
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
 if(result!=WR_IOT_DRIVER_NOT_SUBMITTED){
  attempt->identity=identity;memcpy(attempt->request_id,request.request_id,16);
 }
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

enum wr_iot_driver_submit_result wr_iot_driver_open_requested(
 const char *id,const struct wr_iot_request *input)
{
 struct wr_iot_driver_attempt attempt;
 return wr_iot_driver_open_requested_tracked(id,input,&attempt);
}
int wr_iot_driver_attempt_refused(const struct wr_iot_driver_attempt *attempt)
{
 struct wr_iot_driver_refusal_result refusal;
 if(!attempt||!attempt->identity.adapter_epoch||!attempt->identity.device_generation)return 0;
 if(!wr_iot_driver_refusal_read(attempt->request_id,&refusal))return 0;
 return refusal.adapter_epoch==attempt->identity.adapter_epoch&&
  refusal.device_generation==attempt->identity.device_generation;
}

int wr_iot_driver_attempt_closed(const struct wr_iot_driver_attempt *attempt,
 struct wr_iot_driver_closed_result *out)
{
 struct wr_iot_driver_closed_result observed;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!attempt||!attempt->identity.adapter_epoch||!attempt->identity.device_generation||
    !wr_iot_driver_closed_configuration_read(attempt->request_id,&observed)||
    observed.adapter_epoch!=attempt->identity.adapter_epoch||
    observed.device_generation!=attempt->identity.device_generation)return 0;
 *out=observed;return 1;
}

int wr_iot_driver_uncertain_read(const struct wr_iot_driver_attempt *attempt,struct wr_iot_driver_uncertain_result *out)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_CLOSED_BYTES]={0};
 struct wr_iot_driver_uncertain_result observed;int fd,result,closed;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!attempt||!attempt->identity.adapter_epoch||!attempt->identity.device_generation||
    !wr_iot_driver_uncertain_query_encode(wire,sizeof(wire),attempt->request_id))return 0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);closed=close(fd);
 if(result||closed||!wr_iot_driver_uncertain_decode(&observed,attempt->request_id,wire,sizeof(wire))||
    observed.adapter_epoch!=attempt->identity.adapter_epoch||
    observed.device_generation!=attempt->identity.device_generation)return 0;
 *out=observed;return 1;
}

int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt *attempt,
 struct wr_iot_driver_open_current_result *out)
{
 struct ifreq request={0};unsigned char wire[64]={0};int fd,result,closed;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!attempt||!attempt->identity.adapter_epoch||!attempt->identity.device_generation||
    !wr_iot_driver_open_current_query_encode(wire,sizeof(wire),attempt->request_id))return 0;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return 0;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);closed=close(fd);
 if(result||closed)return 0;
 return wr_iot_driver_open_current_decode(out,attempt->request_id,
   attempt->identity.adapter_epoch,attempt->identity.device_generation,wire,sizeof(wire));
}

int wr_iot_driver_close_request_from_open(struct wr_iot_driver_close_request *out,
 const struct wr_iot_driver_attempt *attempt,const struct wr_iot_driver_open_current_result *current)
{
 unsigned int i,nonzero=0;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!attempt||!current||!attempt->identity.adapter_epoch||
    !attempt->identity.device_generation||!current->open_token||
    current->adapter_epoch!=attempt->identity.adapter_epoch||
    current->device_generation!=attempt->identity.device_generation)return 0;
 for(i=0;i<sizeof(attempt->request_id);i++)nonzero|=attempt->request_id[i];
 if(!nonzero)return 0;
 memcpy(out->open_request_id,attempt->request_id,sizeof(out->open_request_id));
 out->adapter_epoch=current->adapter_epoch;
 out->device_generation=current->device_generation;
 out->open_token=current->open_token;
 return 1;
}

/* The operation result covers the kernel call only. Keep the original OPEN
 * identity and network isolation until the controller completes recovery. */
static enum wr_iot_driver_close_submit_result wr_iot_driver_close_exchange(
 const struct wr_iot_driver_close_request *input,int progress)
{
 struct ifreq request={0};unsigned char wire[WR_IOT_DRIVER_CLOSE_REQUEST_BYTES];
 int fd,result,closed,saved_error;
 if(!(progress?wr_iot_driver_close_progress_encode(wire,sizeof(wire),input):
                wr_iot_driver_close_request_encode(wire,sizeof(wire),input)))
  return WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
 if(fd<0)return WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED;
 memcpy(request.ifr_name,"ra2",4);request.ifr_data=(char *)wire;
 result=ioctl(fd,WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG,&request);
 saved_error=errno;closed=close(fd);
 if(closed)return WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 if(!result)return WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 if(progress&&(saved_error==EAGAIN||saved_error==EINPROGRESS))
  return WR_IOT_DRIVER_CLOSE_PENDING;
 return WR_IOT_DRIVER_CLOSE_UNCERTAIN;
}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_submit(
 const struct wr_iot_driver_close_request *input)
{
 return wr_iot_driver_close_exchange(input,0);
}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_progress_submit(
 const struct wr_iot_driver_close_request *input)
{
 return wr_iot_driver_close_exchange(input,1);
}
