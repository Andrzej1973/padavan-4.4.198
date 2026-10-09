#define _GNU_SOURCE
#include "dhcp-ready.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>
static void response(unsigned char *reply,const unsigned char *query){
 memcpy(reply,query,300);reply[0]=2;memset(reply+240,0,60);
 reply[240]=53;reply[241]=1;reply[242]=5;reply[243]=54;reply[244]=4;reply[245]=127;reply[248]=1;reply[249]=255;
}
int main(int argc,char **argv){
 unsigned char query[300]={0},reply[300];struct sockaddr_in address,client;
 socklen_t len=sizeof(address);pid_t child;int fd,status;
 if(argc==3){int ok=wr_iot_dhcp_ready_at(argv[2],(unsigned int)strtoul(argv[1],NULL,10));puts(ok?"PASS local DHCPINFORM handler response":"FAIL local DHCPINFORM handler response");return ok?0:1;}
 {char gateway[16];assert(wr_iot_dhcp_gateway("lo",gateway)&&!strcmp(gateway,"127.0.0.1"));assert(!wr_iot_dhcp_gateway("nonexistent",gateway));}
 query[0]=1;query[1]=1;query[2]=6;query[4]=1;query[12]=192;query[13]=168;query[14]=1;query[15]=1;query[28]=2;query[33]=253;
 query[236]=99;query[237]=130;query[238]=83;query[239]=99;
 response(reply,query);assert(wr_iot_dhcp_inform_reply(reply,300,query));
 reply[4]++;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 reply[16]=192;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 reply[242]=2;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 reply[12]++;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 reply[33]++;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 reply[236]++;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 memset(reply+245,0,4);assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 reply[249]=52;reply[250]=1;reply[251]=1;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 assert(!wr_iot_dhcp_inform_reply(reply,249,query));
 reply[249]=51;reply[250]=4;assert(!wr_iot_dhcp_inform_reply(reply,300,query));response(reply,query);
 fd=socket(AF_INET,SOCK_DGRAM,0);assert(fd>=0);memset(&address,0,sizeof(address));address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 assert(!bind(fd,(struct sockaddr *)&address,sizeof(address)));assert(!getsockname(fd,(struct sockaddr *)&address,&len));
 child=fork();assert(child>=0);
 if(!child){struct pollfd wait={fd,POLLIN,0};socklen_t client_len=sizeof(client);
  if(poll(&wait,1,2000)!=1)_exit(2);
  if(recvfrom(fd,query,300,0,(struct sockaddr *)&client,&client_len)!=300)_exit(3);
  if(query[242]!=8||query[248]!=255)_exit(4);
  response(reply,query);if(sendto(fd,reply,300,0,(struct sockaddr *)&client,client_len)!=300)_exit(5);
  close(fd);_exit(0);
 }
 close(fd);assert(wr_iot_dhcp_ready_at("192.168.1.1",ntohs(address.sin_port)));
 assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
 assert(!wr_iot_dhcp_ready_at("invalid",67));assert(!wr_iot_dhcp_ready_at("192.168.1.1",0));
 puts("PASS bounded local DHCPINFORM packet and socket checks; production binding pending");return 0;
}
