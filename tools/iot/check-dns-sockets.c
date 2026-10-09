#define _GNU_SOURCE
#include "dns-sockets.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <assert.h>
#include <sys/wait.h>
int main(int argc,char **argv){
 struct sockaddr_in address;socklen_t len=sizeof(address);struct wr_iot_dns_sockets state={0};int tcp,udp;
 state.dns_port=999;state.dhcp_standard=99;
 if(argc==4&&!strcmp(argv[1],"--udp-port")){if(!wr_iot_dns_selected_sockets(argv[2],&state)||!wr_iot_dns_has_udp_port(&state,(unsigned int)strtoul(argv[3],NULL,10)))return 1;puts("PASS trusted daemon owns requested UDP port");return 0;}
 if(argc==3&&!strcmp(argv[1],"--executable")){if(!wr_iot_dns_selected_sockets(argv[2],&state))return 1;printf("{\"dns_port\":%u,\"dhcp_standard\":%d}\n",state.dns_port,state.dhcp_standard);return 0;}
 if(argc==2||argc==3){pid_t pid=(pid_t)strtol(argv[1],NULL,10);if(!(argc==3?wr_iot_dns_daemon_sockets(pid,argv[2],&state):wr_iot_dns_process_sockets(pid,&state)))return 1;printf("{\"dns_port\":%u,\"dhcp_standard\":%d}\n",state.dns_port,state.dhcp_standard);return 0;}
 {struct wr_iot_dns_process_identity first,second;unsigned long long start=99;
  assert(wr_iot_dns_process_identity(getpid(),&first));assert(wr_iot_dns_process_identity(getpid(),&second));assert(wr_iot_dns_same_process(&first,&second));
  second.start++;assert(!wr_iot_dns_same_process(&first,&second));
  assert(!wr_iot_dns_start_time("invalid",&start)&&start==99);
 }
 {pid_t selected=-1,child;int pipes[2],status;char signal;
  assert(wr_iot_dns_unique_daemon("/proc/self/exe",&selected)&&selected==getpid());
  assert(!wr_iot_dns_unique_daemon("/dev/null",&selected)&&selected==getpid());
  assert(!pipe(pipes));child=fork();assert(child>=0);
  if(!child){close(pipes[1]);if(read(pipes[0],&signal,1)!=1)_exit(2);close(pipes[0]);_exit(0);}
  close(pipes[0]);selected=-1;assert(!wr_iot_dns_unique_daemon("/proc/self/exe",&selected)&&selected==-1);
  assert(write(pipes[1],"x",1)==1);close(pipes[1]);assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
  assert(wr_iot_dns_selected_sockets("/proc/self/exe",&state)&&!state.dns_port);
 }
 assert(wr_iot_dns_daemon_sockets(getpid(),"/proc/self/exe",&state)&&!state.dns_port);
 state.dns_port=999;assert(!wr_iot_dns_daemon_sockets(getpid(),"/dev/null",&state)&&state.dns_port==999);
 assert(!wr_iot_dns_daemon_sockets(getpid(),"/definitely-missing-dnsmasq",&state)&&state.dns_port==999);
 tcp=socket(AF_INET,SOCK_STREAM,0);assert(tcp>=0);memset(&address,0,sizeof(address));address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 assert(!bind(tcp,(struct sockaddr *)&address,sizeof(address)));assert(!listen(tcp,1));assert(!getsockname(tcp,(struct sockaddr *)&address,&len));
 udp=socket(AF_INET,SOCK_DGRAM,0);assert(udp>=0);assert(!bind(udp,(struct sockaddr *)&address,sizeof(address)));
 assert(wr_iot_dns_process_sockets(getpid(),&state)&&state.dns_port==ntohs(address.sin_port)&&!state.dhcp_standard&&wr_iot_dns_has_udp_port(&state,ntohs(address.sin_port)));
 close(tcp);assert(wr_iot_dns_process_sockets(getpid(),&state)&&!state.dns_port);close(udp);
 state.dns_port=999;assert(!wr_iot_dns_process_sockets(-1,&state)&&state.dns_port==999);
 puts("PASS bounded process-owned Linux DNS socket inventory; executable identity checked; production binding pending");return 0;
}
