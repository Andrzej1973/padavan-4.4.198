#include "dhcp.h"
#include <assert.h>
int main(void) {
 char out[512],before[512];struct wr_iot_range lan={0xc0a80100,0xc0a801ff};
 const char *expected="interface=br-iot\ndhcp-range=set:wr-iot,192.168.50.20,192.168.50.200,255.255.255.0,3600\ndhcp-option=tag:wr-iot,3,192.168.50.1\ndhcp-option=tag:wr-iot,6,192.168.50.1\n";
 assert(wr_iot_dhcp_fragment(out,sizeof(out),0,0,NULL,NULL,NULL,NULL,NULL,0));assert(!out[0]);
 assert(wr_iot_dhcp_fragment(out,sizeof(out),1,1,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1));assert(!strcmp(out,expected));
 memset(before,0xa5,sizeof(before));memcpy(out,before,sizeof(out));
 assert(!wr_iot_dhcp_fragment(out,sizeof(out),1,0,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_dhcp_fragment(out,20,1,1,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_dhcp_fragment(out,sizeof(out),1,1,"192.168.1.1","255.255.255.0","192.168.1.20","192.168.1.200",&lan,1));assert(!memcmp(out,before,sizeof(out)));
 assert(!wr_iot_dhcp_fragment(out,sizeof(out),1,1,"192.168.50.1\ninterface=br0","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1));assert(!memcmp(out,before,sizeof(out)));
 puts("PASS IoT DHCP fragment candidate: scoped interface/range/options, OFF empty, AP reject, overlap/injection/bounds reject before output");return 0;
}
