#define _GNU_SOURCE
#include "dns-ready.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>
int main(int argc,char **argv){
 unsigned char query[30]={1,2,0,0,0,1,0,0,0,0,0,0,7,'v','e','r','s','i','o','n',4,'b','i','n','d',0,0,16,0,3},reply[46]={0};
 struct sockaddr_in address,client;socklen_t len=sizeof(address);int fd,status,mode;pid_t child;
 if(argc==2||argc==3){int ok=wr_iot_dns_handler_ready_at(argc==3?argv[2]:"127.0.0.1",(unsigned int)strtoul(argv[1],NULL,10));puts(ok?"PASS local DNS handler response":"FAIL local DNS handler response");return ok?0:1;}
 memcpy(reply,query,30);reply[2]=128;reply[7]=1;reply[30]=192;reply[31]=12;reply[33]=16;reply[35]=3;reply[41]=4;reply[42]=3;memcpy(reply+43,"abc",3);
 assert(wr_iot_dns_handler_reply(reply,46,query,30));assert(!wr_iot_dns_handler_reply(reply,45,query,30));
 reply[7]=0;reply[3]=4;assert(wr_iot_dns_handler_reply(reply,30,query,30));
 reply[3]=2;assert(!wr_iot_dns_handler_reply(reply,30,query,30));
 for(mode=0;mode<2;mode++){
  fd=socket(AF_INET,SOCK_DGRAM,0);assert(fd>=0);memset(&address,0,sizeof(address));address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
  assert(!bind(fd,(struct sockaddr *)&address,sizeof(address)));assert(!getsockname(fd,(struct sockaddr *)&address,&len));
  child=fork();assert(child>=0);
  if(!child){struct pollfd wait={fd,POLLIN,0};socklen_t client_len=sizeof(client);
   if(poll(&wait,1,2000)!=1)_exit(2);
   if(recvfrom(fd,query,30,0,(struct sockaddr *)&client,&client_len)!=30)_exit(3);
   memcpy(reply,query,30);reply[2]=128;reply[3]=mode?2:4;reply[7]=0;
   if(sendto(fd,reply,30,0,(struct sockaddr *)&client,client_len)!=30)_exit(4);
   close(fd);_exit(0);
  }
  close(fd);assert(wr_iot_dns_handler_ready(ntohs(address.sin_port))==!mode);
  assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
 }
 puts("PASS local DNS handler TXT/no-ident response checks; production binding pending");return 0;
}
