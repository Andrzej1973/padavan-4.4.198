#define _GNU_SOURCE
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <poll.h>
#include <time.h>
#include <errno.h>
#include "status-channel.h"
#include "precreated-entropy.h"
#define QUERY_BYTES 84
static unsigned long long status_ms(void)
{
 struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t)||t.tv_sec<=0)return 0;
 return (unsigned long long)t.tv_sec*1000+(unsigned long long)t.tv_nsec/1000000;
}
static int peer(int fd,pid_t pid,uid_t uid)
{
 struct ucred p;struct sockaddr_un address;int type;
 socklen_t n=sizeof(p),a=sizeof(address),b=sizeof(type);
 return fd>=0&&!getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&p,&n)&&n==sizeof(p)&&
  p.uid==uid&&p.pid>0&&(!pid||p.pid==pid)&&
  !getsockopt(fd,SOL_SOCKET,SO_TYPE,&type,&b)&&b==sizeof(type)&&type==SOCK_SEQPACKET&&
  !getsockname(fd,(struct sockaddr *)&address,&a)&&address.sun_family==AF_UNIX;
}
static void put_time(unsigned char *p,unsigned long long t)
{unsigned i;for(i=0;i<8;i++)p[i]=(unsigned char)(t>>(56-8*i));}
static unsigned long long get_time(const unsigned char *p)
{unsigned i;unsigned long long t=0;for(i=0;i<8;i++)t=(t<<8)|p[i];return t;}
static int record_valid(const struct wr_iot_control_result *r,unsigned long long now)
{
 return r&&r->state==WR_IOT_RESULT_APPLIED&&memchr(r->id,0,sizeof(r->id))&&
  wr_iot_control_id(r->id)&&r->created&&r->created<=r->observed&&r->observed<=now;
}
int wr_iot_status_query(int fd,pid_t rc_pid,uid_t uid,const struct wr_iot_control_result *r)
{
 unsigned char query[QUERY_BYTES],reply[QUERY_BYTES+1];struct pollfd p={fd,POLLIN,0};
 unsigned long long now=status_ms(),deadline;ssize_t n;int ready;
 if(!now||rc_pid<=0||!peer(fd,rc_pid,uid)||!record_valid(r,now/1000))return 0;
 memcpy(query,"WIS1",4);memcpy(query+4,r->id,32);
 put_time(query+36,r->created);put_time(query+44,r->observed);
 if(wr_iot_precreated_entropy(NULL,query+52,32)!=32)return 0;
 if(send(fd,query,sizeof(query),MSG_DONTWAIT|MSG_NOSIGNAL)!=(ssize_t)sizeof(query))return 0;
 deadline=now+1000;
 do {
  now=status_ms();if(!now||now>=deadline)return 0;
  ready=poll(&p,1,(int)(deadline-now));
 }while(ready<0&&errno==EINTR);
 if(ready<=0||!(p.revents&POLLIN))return 0;
 n=recv(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_TRUNC);
 return n==(ssize_t)sizeof(reply)&&!memcmp(reply,query,sizeof(query))&&reply[QUERY_BYTES]==1&&peer(fd,rc_pid,uid);
}
int wr_iot_status_serve_once(int fd,uid_t uid,int (*observe)(const struct wr_iot_control_result *))
{
 unsigned char query[QUERY_BYTES],reply[QUERY_BYTES+1];struct wr_iot_control_result r={0};
 unsigned long long now=status_ms();ssize_t n;int valid;
 if(!observe||!now||!peer(fd,0,uid))return 0;
 n=recv(fd,query,sizeof(query),MSG_DONTWAIT|MSG_TRUNC);
 if(n!=(ssize_t)sizeof(query)||memcmp(query,"WIS1",4))return 0;
 memcpy(r.id,query+4,32);r.created=get_time(query+36);r.observed=get_time(query+44);
 r.state=WR_IOT_RESULT_APPLIED;
 if(!record_valid(&r,now/1000))return 0;
 valid=observe(&r)==1;
 memcpy(reply,query,sizeof(query));reply[QUERY_BYTES]=(unsigned char)valid;
 return send(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_NOSIGNAL)==(ssize_t)sizeof(reply);
}
