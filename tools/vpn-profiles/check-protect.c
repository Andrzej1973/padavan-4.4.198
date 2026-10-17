#include "protect.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    char buffer[128];const char *out[8];
    int count;

    count=wr_vpn_parse_protect("192.168.20.0/24, 172.16.0.0/12\t, fd00::/64",
                               buffer,sizeof(buffer),out,8);
    assert(count==3);
    assert(!strcmp(out[0],"192.168.20.0/24"));
    assert(!strcmp(out[1],"172.16.0.0/12"));
    assert(!strcmp(out[2],"fd00::/64"));

    assert(wr_vpn_parse_protect("",buffer,sizeof(buffer),out,8)==0);

    /* Empty tokens and more prefixes than the caller can hold refuse. */
    assert(wr_vpn_parse_protect(" , 10.0.0.0/8",buffer,sizeof(buffer),out,8)==-1);
    assert(wr_vpn_parse_protect("1.1.1.1/32,,2.2.2.2/32",buffer,sizeof(buffer),out,8)==-1);
    assert(wr_vpn_parse_protect("1.0.0.0/8,2.0.0.0/8,3.0.0.0/8",
                                buffer,sizeof(buffer),out,2)==-1);
    assert(wr_vpn_parse_protect("2001:db8::/32",buffer,4,out,8)==-1);

    puts("PASS protected-prefix parse: whitespace trim, empty/overflow refusal");
    return 0;
}
