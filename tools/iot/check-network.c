#include "network-check.h"
#include "bridge.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
int main(void) {
 char current[128];const char *parent=getenv("WR_IOT_PARENT_NETNS");ssize_t n;int fd;FILE *alias;struct ifreq request;
 n=readlink("/proc/self/ns/net",current,sizeof(current)-1);
 if(geteuid()!=0||!parent||n<0)return 2;
 current[n]=0;if(!strcmp(current,parent))return 2;
 assert(wr_iot_network_check("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200"));
 assert(!wr_iot_network_check("192.168.1.1","255.255.255.0","192.168.1.20","192.168.1.200"));
 assert(!wr_iot_network_check("10.88.0.1","255.255.255.0","10.88.0.20","10.88.0.200"));
 assert(!wr_iot_network_check("192.168.50.1","255.0.255.0","192.168.50.20","192.168.50.200"));
 assert(wr_iot_bridge_prepare("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",NULL,0));
 assert(wr_iot_bridge_is_owned());
 fd=socket(AF_INET,SOCK_DGRAM,0);assert(fd>=0);memset(&request,0,sizeof(request));strcpy(request.ifr_name,"br-iot");
 assert(ioctl(fd,SIOCGIFFLAGS,&request)==0);request.ifr_flags|=IFF_UP;assert(ioctl(fd,SIOCSIFFLAGS,&request)==0);close(fd);
 assert(wr_iot_network_check("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200"));
 alias=fopen("/sys/class/net/br-iot/ifalias","w");assert(alias);assert(fputs("foreign-fixture\n",alias)>=0);assert(!fclose(alias));
 assert(!wr_iot_bridge_is_owned());
 assert(!wr_iot_network_check("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200"));
 puts("PASS actual network validator: LAN/VPN conflicts and invalid mask rejected; disjoint candidate and owned bridge accepted; foreign bridge conflict rejected");return 0;
}
