#include <assert.h>
#include <stdio.h>
#include "config.h"
int main(void)
{
 struct wr_eoip_config c;unsigned n;
 assert(wr_eoip_validate("0","1","1","0.0.0.0","192.168.30.1","65535","1458","10","10","br0",&c));
 assert(c.tunnel_id==65535&&c.mtu==1458&&c.keepalive==10&&c.retries==10&&!strcmp(c.bridge,"br0"));
 assert(wr_eoip_validate("7","0","0","192.168.20.1","192.168.30.1","0","68","0","255","",&c));
 assert(c.retries==0&&!c.bridge[0]);
 assert(wr_eoip_decimal("65486",WR_EOIP_MAX_MTU,&n)&&n==WR_EOIP_MAX_MTU);
 assert(!wr_eoip_decimal("65487",WR_EOIP_MAX_MTU,&n));
 assert(!wr_eoip_decimal("-1",65535,&n)&&!wr_eoip_decimal("1;id",65535,&n));
 assert(!wr_eoip_decimal("9999999999",65535,&n)&&!wr_eoip_decimal("1\n",65535,&n));
 assert(!wr_eoip_ipv4("0.0.0.0",0,&c.remote)&&!wr_eoip_ipv4("127.0.0.1",0,&c.remote));
 assert(!wr_eoip_ipv4("224.0.0.1",0,&c.remote)&&!wr_eoip_ipv4("255.255.255.255",0,&c.remote));
 assert(!wr_eoip_ipv4("::1",0,&c.remote)&&!wr_eoip_ipv4("10.1.2.3;id",0,&c.remote));
 assert(!wr_eoip_validate("8","1","0","0.0.0.0","10.0.0.2","1","1458","0","0","br0",&c));
 assert(!wr_eoip_validate("0","1","0","10.0.0.2","10.0.0.2","1","1458","0","0","br0",&c));
 assert(!wr_eoip_validate("0","1","0","0.0.0.0","10.0.0.2","65536","1458","0","0","br0",&c));
 assert(!wr_eoip_validate("0","1","0","0.0.0.0","10.0.0.2","1","67","0","0","br0",&c));
 assert(!wr_eoip_validate("0","1","0","0.0.0.0","10.0.0.2","1","1458","3601","0","br0",&c));
 assert(!wr_eoip_validate("0","1","0","0.0.0.0","10.0.0.2","1","1458","10","256","br0",&c));
 assert(!wr_eoip_validate("0","1","0","0.0.0.0","10.0.0.2","1","1458","0","0","../br0",&c));
 assert(c.enabled==0&&c.remote.s_addr==0);
 puts("PASS EoIP configuration: IPv4, ID, MTU, keepalive, bridge syntax, cleared failures");
 return 0;
}
