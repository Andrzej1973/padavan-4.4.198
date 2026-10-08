#include "firewall.h"
#include <assert.h>
int main(void) {
 struct wr_iot_firewall out,before;struct wr_iot_range lan={0xc0a80100,0xc0a801ff};
 assert(wr_iot_firewall_plan(&out,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0));assert(!out.ipv4[0]&&!out.ipv6[0]);
 assert(wr_iot_firewall_plan(&out,1,"br0","eth2.2","192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1));
 assert(strstr(out.ipv4,"--dst-range 192.168.1.0-192.168.1.255 -j DROP"));
 assert(strstr(out.ipv4,"-A INPUT -i br-iot -j DROP"));
 assert(strstr(out.ipv4,"-A FORWARD -i br-iot -o eth2.2 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT"));
 assert(strstr(out.ipv4,"--dst-range")<strstr(out.ipv4,"-o eth2.2"));
 assert(!strstr(out.ipv4,"--dport 22")&&!strstr(out.ipv4,"--dport 80"));
 assert(strstr(out.ipv6,"-A FORWARD -o br-iot -j DROP"));
 assert(wr_iot_firewall_plan(&out,1,"br0","","192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1));
 assert(!strstr(out.ipv4,"NEW,ESTABLISHED,RELATED -j ACCEPT"));
 memset(&before,0xa5,sizeof(before));out=before;
#define BAD(w,c) do {assert(!wr_iot_firewall_plan(&out,1,"br0",w,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,c));assert(!memcmp(&out,&before,sizeof(out)));} while(0)
 BAD("br0",1);BAD("br-iot",1);BAD("eth2.2\n-j ACCEPT",1);BAD("eth2.2",17);
 puts("PASS IoT firewall fragment candidate: ordered isolation, scoped DHCP/DNS, WAN-only forwarding, no-WAN drop, IPv6 drop, bounded input; packet behavior unverified");return 0;
}
