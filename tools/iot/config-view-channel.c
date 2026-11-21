#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/un.h>
#include <poll.h>
#include <time.h>
#include <errno.h>
#include "config-view-channel.h"
#include "control-record-common.h"
#include "precreated-entropy.h"
#define VIEW_QUERY_BYTES 36
#define VIEW_REPLY_BYTES 168
static unsigned long long milliseconds(void)
{
 struct timespec now;
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    (unsigned long long)now.tv_sec>(~0ULL-999)/1000)return 0;
 return (unsigned long long)now.tv_sec*1000+(unsigned long long)now.tv_nsec/1000000;
}
static int peer(int fd,pid_t pid,uid_t uid)
{
 struct ucred credentials;struct sockaddr_un address;int type;
 socklen_t size=sizeof(credentials),address_size=sizeof(address),type_size=sizeof(type);
 if(fd<0||getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&credentials,&size)||size!=sizeof(credentials)||
    credentials.pid<=0||credentials.uid!=uid||(pid&&credentials.pid!=pid)||
    getsockopt(fd,SOL_SOCKET,SO_TYPE,&type,&type_size)||type_size!=sizeof(type)||type!=SOCK_SEQPACKET||
    getsockname(fd,(struct sockaddr *)&address,&address_size)||address.sun_family!=AF_UNIX)return 0;
 address_size=sizeof(address);
 return !getpeername(fd,(struct sockaddr *)&address,&address_size)&&address.sun_family==AF_UNIX;
}
static int nonce_valid(const unsigned char *bytes)
{
 size_t index;unsigned char nonzero=0;
 for(index=0;index<32;index++)nonzero|=bytes[index];
 return nonzero!=0;
}
int wr_iot_config_view_query(int fd,pid_t rc_pid,uid_t uid,
 struct wr_iot_config_view *out,char revision[33])
{
 unsigned char query[VIEW_QUERY_BYTES]={0},reply[VIEW_REPLY_BYTES]={0};
 struct wr_iot_config_view view={0};char token[33]={0};
 struct pollfd event={fd,POLLIN,0};unsigned long long now=milliseconds(),deadline;
 int ready,ok=0;ssize_t bytes;
 if(!out||!revision||rc_pid<=0||!now||now>~0ULL-1000||!peer(fd,rc_pid,uid))goto done;
 memcpy(query,"WIQ1",4);
 if(wr_iot_precreated_entropy(NULL,query+4,32)!=32||!nonce_valid(query+4))goto done;
 if(send(fd,query,sizeof(query),MSG_DONTWAIT|MSG_NOSIGNAL)!=(ssize_t)sizeof(query))goto done;
 deadline=now+1000;
 for(;;){
  now=milliseconds();if(!now||now>=deadline)goto done;
  ready=poll(&event,1,(int)(deadline-now));
  if(ready<0&&errno==EINTR)continue;
  if(ready<=0||!(event.revents&POLLIN))goto done;
  break;
 }
 bytes=recv(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_TRUNC);
 if(bytes!=(ssize_t)sizeof(reply)||memcmp(reply,"WIV1",4)||memcmp(reply+4,query+4,32)||
    reply[36]!=1||!peer(fd,rc_pid,uid))goto done;
 memcpy(token,reply+37,32);view.enabled=reply[69];view.key_present=reply[70];
 memcpy(view.ssid,reply+71,33);memcpy(view.gateway,reply+104,16);
 memcpy(view.mask,reply+120,16);memcpy(view.first,reply+136,16);memcpy(view.last,reply+152,16);
 if(!wr_iot_control_id(token)||!wr_iot_config_view_valid(&view))goto done;
 *out=view;memcpy(revision,token,sizeof(token));ok=1;
 done:wr_iot_saved_wipe(query,sizeof(query));wr_iot_saved_wipe(reply,sizeof(reply));
 wr_iot_saved_wipe(&view,sizeof(view));wr_iot_saved_wipe(token,sizeof(token));return ok;
}
int wr_iot_config_view_serve_once(int fd,uid_t uid,unsigned int lifetime,
 int (*capture)(unsigned int,struct wr_iot_config_view *,char[33]))
{
 unsigned char query[VIEW_QUERY_BYTES]={0},reply[VIEW_REPLY_BYTES]={0};
 struct wr_iot_config_view view={0};char token[33]={0};int ok=0;
 if(!capture||!lifetime||lifetime>300||!peer(fd,0,uid)||
    recv(fd,query,sizeof(query),MSG_DONTWAIT|MSG_TRUNC)!=(ssize_t)sizeof(query)||
    memcmp(query,"WIQ1",4)||!nonce_valid(query+4))goto done;
 memcpy(reply,"WIV1",4);memcpy(reply+4,query+4,32);
 if(capture(lifetime,&view,token)==1&&memchr(token,0,sizeof(token))&&wr_iot_control_id(token)&&wr_iot_config_view_valid(&view)){
  reply[36]=1;memcpy(reply+37,token,32);reply[69]=(unsigned char)view.enabled;reply[70]=(unsigned char)view.key_present;
  memcpy(reply+71,view.ssid,33);memcpy(reply+104,view.gateway,16);memcpy(reply+120,view.mask,16);
  memcpy(reply+136,view.first,16);memcpy(reply+152,view.last,16);
 }
 if(peer(fd,0,uid))ok=send(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_NOSIGNAL)==(ssize_t)sizeof(reply);
 done:wr_iot_saved_wipe(query,sizeof(query));wr_iot_saved_wipe(reply,sizeof(reply));
 wr_iot_saved_wipe(&view,sizeof(view));wr_iot_saved_wipe(token,sizeof(token));return ok;
}
