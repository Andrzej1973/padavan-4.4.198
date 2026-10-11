#include "network-check.h"
#include "bridge.h"
#include "route-snapshot.h"
#include "subnet.h"
#include "dns-ready.h"
#include "dhcp-ready.h"
#include "dns-sockets.h"
int wr_iot_network_check(const char *gateway,const char *mask,const char *start,const char *end) {
 struct wr_iot_inventory inventory;struct wr_iot_subnet plan;unsigned int owned_index=0;
 if(!wr_iot_subnet_plan(&plan,gateway,mask,start,end,NULL,0))return 0;
 if(wr_iot_bridge_is_owned()) {
  owned_index=if_nametoindex("br-iot");if(!owned_index)return 0;
 }
 if(!wr_iot_inventory_interfaces(&inventory,owned_index!=0)||
    !wr_iot_route_snapshot_owned(&inventory,owned_index,plan.network,plan.mask))return 0;
 return wr_iot_subnet_plan(&plan,gateway,mask,start,end,inventory.ranges,inventory.count);
}

int wr_iot_network_services_ready(const char *gateway) {
 struct wr_iot_dns_sockets sockets;struct ifreq request;
 struct in_addr expected,actual;char address[16];int fd,up;
 if(!gateway||inet_pton(AF_INET,gateway,&expected)!=1||!expected.s_addr||
    !wr_iot_bridge_is_owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,"br-iot");
 up=ioctl(fd,SIOCGIFFLAGS,&request)==0&&(request.ifr_flags&IFF_UP);
 close(fd);
 if(!up||!wr_iot_dhcp_gateway("br-iot",address)||
    inet_pton(AF_INET,address,&actual)!=1||actual.s_addr!=expected.s_addr)return 0;
 /* Socket ownership is necessary but not sufficient: require real replies.
  * DHCPINFORM does not allocate a lease. IoT uses fixed DNS/DHCP ports 53/67. */
 return wr_iot_dns_selected_sockets("/usr/sbin/dnsmasq",&sockets)&&
        sockets.dns_port==53&&wr_iot_dns_has_udp_port(&sockets,67)&&
        wr_iot_dns_handler_ready_at(gateway,53)&&wr_iot_dhcp_ready_at(gateway,67);
}
