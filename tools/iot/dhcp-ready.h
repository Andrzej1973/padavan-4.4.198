/* Local DHCPINFORM probe: no DISCOVER/REQUEST and no lease-time request.
 * This checks the server handler; client-facing subnet/pool checks remain separate. */
#ifndef WR_IOT_DHCP_READY_H
#define WR_IOT_DHCP_READY_H
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <poll.h>
static inline int wr_iot_dhcp_inform_reply(const unsigned char *reply,size_t size,const unsigned char *query){
 size_t p=240;int ack=0,server=0,ended=0;
 if(!reply||!query||size<240||reply[0]!=2||reply[1]!=1||reply[2]!=6||
    memcmp(reply+4,query+4,4)||memcmp(reply+12,query+12,4)||
    reply[16]||reply[17]||reply[18]||reply[19]||memcmp(reply+28,query+28,6)||
    memcmp(reply+236,query+236,4))return 0;
 while(p<size){
  unsigned int key=reply[p++],n;
  if(key==255){ended=1;break;}
  if(!key)continue;
  if(p>=size)return 0;
  n=reply[p++];if(size-p<n)return 0;
  if(key==53){if(ack||n!=1||reply[p]!=5)return 0;ack=1;}
  if(key==54){if(server||n!=4||!(reply[p]|reply[p+1]|reply[p+2]|reply[p+3]))return 0;server=1;}
  if(key==51||key==52)return 0; /* No lease-time or overloaded option areas requested. */
  p+=n;
 }
 return ack&&server&&ended;
}
static inline int wr_iot_dhcp_ready_at(const char *client_address,unsigned int port){
 unsigned char query[300]={0},reply[1024];struct in_addr client;
 struct sockaddr_in address;struct pollfd wait;static uint32_t sequence;
 uint32_t id;int fd,ok=0;ssize_t size;
 if(!client_address||!port||port>65535||inet_pton(AF_INET,client_address,&client)!=1||!client.s_addr)return 0;
 query[0]=1;query[1]=1;query[2]=6;id=htonl(++sequence^(uint32_t)getpid());memcpy(query+4,&id,4);
 memcpy(query+12,&client,4);query[28]=2;query[33]=253;
 query[236]=99;query[237]=130;query[238]=83;query[239]=99;
 query[240]=53;query[241]=1;query[242]=8;query[243]=55;query[244]=3;query[245]=1;query[246]=3;query[247]=6;query[248]=255;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&address,0,sizeof(address));address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 if(bind(fd,(struct sockaddr *)&address,sizeof(address)))goto done;
 address.sin_port=htons((uint16_t)port);
 if(connect(fd,(struct sockaddr *)&address,sizeof(address))||send(fd,query,sizeof(query),0)!=(ssize_t)sizeof(query))goto done;
 wait.fd=fd;wait.events=POLLIN;wait.revents=0;
 if(poll(&wait,1,200)!=1||!(wait.revents&POLLIN))goto done;
 size=recv(fd,reply,sizeof(reply),MSG_DONTWAIT|MSG_TRUNC);
 if(size>=0&&(size_t)size<=sizeof(reply))ok=wr_iot_dhcp_inform_reply(reply,(size_t)size,query);
 done:close(fd);return ok;
}
#endif
