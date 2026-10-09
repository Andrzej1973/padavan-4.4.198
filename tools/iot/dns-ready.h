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
/* Verify every declared record is present before treating a packet as ready. */
static inline int wr_iot_dns_name_span(const unsigned char *data,size_t size,size_t *offset){
 size_t p,end=0;unsigned int steps=0;
 if(!data||!offset||*offset>=size)return 0;
 p=*offset;
 while(p<size&&++steps<=128){
  unsigned int n=data[p];
  if(!n){if(!end)end=p+1;*offset=end;return 1;}
  if((n&192)==192){size_t target;if(size-p<2)return 0;target=((size_t)(n&63)<<8)|data[p+1];if(target<12||target>=p)return 0;if(!end)end=p+2;p=target;continue;}
  if(n>63||size-p-1<n)return 0;
  p+=n+1;
 }
 return 0;
}
static inline int wr_iot_dns_records_complete(const unsigned char *data,size_t size,size_t offset){
 unsigned int count,i;size_t n;
 if(!data||size<12||offset>size)return 0;
 count=((unsigned int)data[6]<<8)|data[7];count+=((unsigned int)data[8]<<8)|data[9];count+=((unsigned int)data[10]<<8)|data[11];
 if(count>64)return 0;
 for(i=0;i<count;i++){
  if(!wr_iot_dns_name_span(data,size,&offset)||size-offset<10)return 0;
  n=((size_t)data[offset+8]<<8)|data[offset+9];offset+=10;
  if(size-offset<n)return 0;
  offset+=n;
 }
 return offset==size;
}
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
  return length==4&&size-pos-10>=length&&wr_iot_dns_records_complete(reply,size,query_size);
 }
}
/* CHAOS version.bind is answered locally by pinned dnsmasq even without hosts.
 * With no-ident it returns NOTIMP locally, which confirms handler readiness.
 * This does not establish external DNS resolution or forwarding health. */
static inline int wr_iot_dns_handler_reply(const unsigned char *reply,size_t size,const unsigned char *query,size_t query_size){
 unsigned int code;size_t pos,length,end;
 if(!reply||!query||query_size!=30||size<query_size||memcmp(reply,query,2)||
    !(reply[2]&128)||(reply[2]&122)||reply[4]||reply[5]!=1||memcmp(reply+12,query+12,18)||
    !wr_iot_dns_records_complete(reply,size,query_size))return 0;
 code=reply[3]&15;
 if(code==4)return !reply[6]&&!reply[7]&&!reply[8]&&!reply[9];
 if(code||(!reply[6]&&!reply[7]))return 0;
 pos=query_size;
 if(size-pos>=2&&reply[pos]==192&&reply[pos+1]==12)pos+=2;
 else if(size-pos>=14&&!memcmp(reply+pos,query+12,14))pos+=14;
 else return 0;
 if(size-pos<10||reply[pos]||reply[pos+1]!=16||reply[pos+2]||reply[pos+3]!=3)return 0;
 length=((size_t)reply[pos+8]<<8)|reply[pos+9];pos+=10;
 if(!length||size-pos<length)return 0;
 end=pos+length;
 while(pos<end){length=reply[pos++];if(end-pos<length)return 0;pos+=length;}
 return pos==end;
}
static inline int wr_iot_dns_handler_ready(unsigned int port){
 unsigned char query[30]={0,0,0,0,0,1,0,0,0,0,0,0,7,'v','e','r','s','i','o','n',4,'b','i','n','d',0,0,16,0,3};
 unsigned char reply[512];struct sockaddr_in address;struct pollfd wait;
 static uint16_t sequence;int fd,ok=0;ssize_t size;
 if(!port||port>65535)return 0;
 sequence++;query[0]=(unsigned char)((sequence^(uint16_t)getpid())>>8);query[1]=(unsigned char)(sequence^(uint16_t)getpid());
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&address,0,sizeof(address));address.sin_family=AF_INET;address.sin_port=htons((uint16_t)port);address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 if(connect(fd,(struct sockaddr *)&address,sizeof(address))||send(fd,query,sizeof(query),0)!=(ssize_t)sizeof(query))goto done;
 wait.fd=fd;wait.events=POLLIN;wait.revents=0;
 if(poll(&wait,1,200)!=1||!(wait.revents&POLLIN))goto done;
 size=recv(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_TRUNC);
 if(size>=0&&(size_t)size<=sizeof(reply))ok=wr_iot_dns_handler_reply(reply,(size_t)size,query,sizeof(query));
 done:close(fd);return ok;
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
 size=recv(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_TRUNC);
 if(size>=0&&(size_t)size<=sizeof(reply))ok=wr_iot_dns_reply(reply,(size_t)size,query,sizeof(query));
 done:close(fd);return ok;
}
#endif
