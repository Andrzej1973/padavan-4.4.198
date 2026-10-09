/* Bounded local-only DNS probe. Caller selects the configured listening port. */
#ifndef WR_IOT_DNS_READY_H
#define WR_IOT_DNS_READY_H
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <poll.h>
#include <errno.h>
static inline int wr_iot_dns_reply(const unsigned char *reply,size_t size,const unsigned char *query,size_t query_size){
 if(!reply||!query||query_size!=27||size<query_size||reply[0]!=query[0]||reply[1]!=query[1]||
    !(reply[2]&128)||(reply[2]&120)||(reply[2]&2)||(reply[3]&15)||
    reply[4]!=0||reply[5]!=1||(reply[6]==0&&reply[7]==0)||memcmp(reply+12,query+12,15))return 0;
 /* Require the localhost owner, A/IN and a complete IPv4 answer. */
 {size_t pos=query_size;unsigned int length;
  if(size-pos>=2&&reply[pos]==192&&reply[pos+1]==12)pos+=2;
  else if(size-pos>=11&&!memcmp(reply+pos,query+12,11))pos+=11;
  else return 0;
  if(size-pos<10)return 0;
  if(reply[pos]!=0||reply[pos+1]!=1||reply[pos+2]!=0||reply[pos+3]!=1)return 0;
  length=((unsigned int)reply[pos+8]<<8)|reply[pos+9];
  return length==4&&size-pos-10>=length;
 }
}
static inline int wr_iot_dns_ready(unsigned int port){
 unsigned char query[27]={0,0,1,0,0,1,0,0,0,0,0,0,9,'l','o','c','a','l','h','o','s','t',0,0,1,0,1};
 unsigned char reply[512];struct sockaddr_in address;struct pollfd wait;
 static uint16_t sequence;int fd,ok=0;ssize_t size;
 if(!port||port>65535)return 0;
 sequence++;query[0]=(unsigned char)((sequence^(uint16_t)getpid())>>8);query[1]=(unsigned char)(sequence^(uint16_t)getpid());
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&address,0,sizeof(address));address.sin_family=AF_INET;address.sin_port=htons((uint16_t)port);address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 if(connect(fd,(struct sockaddr *)&address,sizeof(address))||send(fd,query,sizeof(query),0)!=(ssize_t)sizeof(query))goto done;
 wait.fd=fd;wait.events=POLLIN;wait.revents=0;
 if(poll(&wait,1,200)!=1||!(wait.revents&POLLIN))goto done;
 size=recv(fd,reply,sizeof(reply),MSG_DONTWAIT);
 if(size>=0)ok=wr_iot_dns_reply(reply,(size_t)size,query,sizeof(query));
 done:close(fd);return ok;
}
#endif
