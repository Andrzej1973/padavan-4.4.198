#define _GNU_SOURCE
#include "dns-ready.h"
#include <assert.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <stdio.h>
static void response(unsigned char *reply,const unsigned char *query){
 memset(reply,0,43);memcpy(reply,query,27);reply[2]=129;reply[3]=128;reply[7]=1;
 reply[27]=192;reply[28]=12;reply[30]=1;reply[32]=1;reply[38]=4;reply[39]=127;reply[42]=1;
}
int main(void){
 unsigned char query[27]={1,2,1,0,0,1,0,0,0,0,0,0,9,'l','o','c','a','l','h','o','s','t',0,0,1,0,1},reply[600]={0};
 struct sockaddr_in server,client;socklen_t len=sizeof(server);int fd,status,mode;pid_t child;
 response(reply,query);assert(wr_iot_dns_reply(reply,43,query,27));assert(!wr_iot_dns_reply(reply,42,query,27));
 reply[0]++;assert(!wr_iot_dns_reply(reply,43,query,27));response(reply,query);
 reply[2]|=2;assert(!wr_iot_dns_reply(reply,43,query,27));response(reply,query);
 reply[3]|=3;assert(!wr_iot_dns_reply(reply,43,query,27));response(reply,query);
 reply[28]=255;assert(!wr_iot_dns_reply(reply,43,query,27));response(reply,query);
 reply[7]=2;assert(!wr_iot_dns_reply(reply,43,query,27));response(reply,query);
 reply[11]=1;assert(!wr_iot_dns_reply(reply,43,query,27));response(reply,query);
 {unsigned char extended[44];memcpy(extended,reply,43);extended[43]=0;assert(!wr_iot_dns_reply(extended,44,query,27));}
 {unsigned char loop[29]={0};size_t offset=27;loop[27]=192;loop[28]=27;assert(!wr_iot_dns_name_span(loop,29,&offset));}
 for(mode=0;mode<2;mode++){
 fd=socket(AF_INET,SOCK_DGRAM,0);assert(fd>=0);memset(&server,0,sizeof(server));server.sin_family=AF_INET;server.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 assert(!bind(fd,(struct sockaddr *)&server,sizeof(server)));assert(!getsockname(fd,(struct sockaddr *)&server,&len));
 child=fork();assert(child>=0);
 if(!child){struct pollfd wait={fd,POLLIN,0};socklen_t client_len=sizeof(client);
  if(poll(&wait,1,2000)!=1)_exit(2);
  if(recvfrom(fd,query,27,0,(struct sockaddr *)&client,&client_len)!=27)_exit(3);
  memset(reply,0,sizeof(reply));response(reply,query);
  if(mode){
   /* A valid 512-byte prefix followed by undeclared data must not pass when truncated. */
   reply[11]=1;reply[43]=192;reply[44]=12;reply[46]=16;reply[48]=1;reply[53]=1;reply[54]=201;
   if(!wr_iot_dns_reply(reply,512,query,27))_exit(5);
  }
  {size_t length=mode?sizeof(reply):43;if(sendto(fd,reply,length,0,(struct sockaddr *)&client,client_len)!=(ssize_t)length)_exit(4);}
  close(fd);_exit(0);
 }
 close(fd);assert(wr_iot_dns_ready(ntohs(server.sin_port))==!mode);assert(waitpid(child,&status,0)==child);assert(WIFEXITED(status)&&WEXITSTATUS(status)==0);
 }
 assert(!wr_iot_dns_ready(0));assert(!wr_iot_dns_ready(65536));
 puts("PASS bounded loopback DNS probe and response checks; complete declared records and compression bounds");return 0;
}
