#include "ip-command-result.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    const char *v4_route[]={"ip","route","del","10.0.0.0/8",NULL};
    const char *v6_route[]={"ip","-6","route","del","::/0",NULL};
    const char *v4_rule[]={"ip","rule","del","fwmark","0x1",NULL};
    const char *v6_rule[]={"ip","-6","rule","del","fwmark","0x1",NULL};
    const char *address[]={"ip","address","del","10.0.0.1/32",NULL};
    const char *add[]={"ip","route","replace","0.0.0.0/0",NULL};
    assert(wr_vpn_ip_delete_absent(v4_route,"RTNETLINK answers: No such process\n"));
    assert(wr_vpn_ip_delete_absent(v6_route,"RTNETLINK answers: No such file or directory\n"));
    assert(wr_vpn_ip_delete_absent(v4_rule,"RTNETLINK answers: No such file or directory\n"));
    assert(wr_vpn_ip_delete_absent(v6_rule,"RTNETLINK answers: No such process\n"));
    assert(wr_vpn_ip_delete_absent(address,"RTNETLINK answers: Cannot assign requested address\n"));
    assert(!wr_vpn_ip_delete_absent(v4_route,"RTNETLINK answers: Cannot find device\n"));
    assert(!wr_vpn_ip_delete_absent(v4_route,"Permission denied\n"));
    assert(!wr_vpn_ip_delete_absent(add,"RTNETLINK answers: No such process\n"));
    assert(wr_vpn_rule_match_listing("",20003,0x57560002,20002)==WR_VPN_RULE_ABSENT);
    assert(wr_vpn_rule_match_listing("20003:\tfrom all fwmark 0x57560002 lookup 20002\n",
        20003,0x57560002,20002)==WR_VPN_RULE_EXACT);
    assert(wr_vpn_rule_match_listing("20003:\tfrom all fwmark 0x57560002 lookup 20002\n"
        "20003:\tfrom 192.0.2.0/24 fwmark 0x57560002 lookup 20002\n",
        20003,0x57560002,20002)==WR_VPN_RULE_AMBIGUOUS);
    assert(wr_vpn_rule_match_listing("20003:\tfrom all fwmark 0x57560002 lookup 20002",
        20003,0x57560002,20002)==WR_VPN_RULE_AMBIGUOUS);
    puts("PASS VPN idempotent-delete error classification");
    return 0;
}
