#include "route-apply.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define MAX_CALLS 32
#define MAX_COMMAND 256
static char recorded[MAX_CALLS][MAX_COMMAND];
static int calls,fail_at,fail_at_second,unknown_at,present_at;

static enum wr_vpn_exec_result record(void *context,const char *const argv[])
{
    size_t used=0;int i,call;
    (void)context;
    call=++calls;
    assert(call<=MAX_CALLS);
    for (i=0;argv[i];i++) {
        int n=snprintf(recorded[call-1]+used,MAX_COMMAND-used,"%s%s",i?" ":"",argv[i]);
        assert(n>=0 && (size_t)n<MAX_COMMAND-used);
        used+=(size_t)n;
    }
    if (call==unknown_at) return WR_VPN_EXEC_UNKNOWN;
    if (call==present_at) return WR_VPN_EXEC_PRESENT;
    return call==fail_at || call==fail_at_second?WR_VPN_EXEC_FAILED:WR_VPN_EXEC_DONE;
}

static const struct wr_vpn_exec exec={record,NULL};
static struct wr_vpn_resources resources;

static enum wr_vpn_route_result run(int add,const char *allowed,int fail_first,
    int fail_second,const char *expected)
{
    enum wr_vpn_route_result result;
    int i;
    memset(&resources,0,sizeof(resources));
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    memset(recorded,0,sizeof(recorded));calls=0;fail_at=fail_first;fail_at_second=fail_second;
    result=wr_vpn_routes_apply(&resources,allowed,add,&exec);
    for (i=0;i<calls;i++) {
        const char *newline=strchr(expected,'\n');size_t length;
        if (!newline) {
            fprintf(stderr,"unexpected extra command %d: %s\n",i,recorded[i]);
            assert(newline);
        }
        length=(size_t)(newline-expected);
        if (strlen(recorded[i])!=length || memcmp(recorded[i],expected,length))
            fprintf(stderr,"command %d expected [%.*s], got [%s]\n",i,(int)length,expected,recorded[i]);
        assert(strlen(recorded[i])==length && !memcmp(recorded[i],expected,length));
        expected=newline+1;
    }
    if (*expected) fprintf(stderr,"missing commands after %d calls: %s",calls,expected);
    assert(!*expected);
    return result;
}

int main(void)
{
    assert(run(1,"0.0.0.0/0",0,0,
        "ip route replace 0.0.0.0/0 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n")
        ==WR_VPN_ROUTE_DONE);

    assert(run(1,"::/0",0,0,
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n")
        ==WR_VPN_ROUTE_DONE);

    assert(run(1,"0.0.0.0/0, ::/0",0,0,
        "ip route replace 0.0.0.0/0 dev wrvpn2 table 20002\n"
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n")
        ==WR_VPN_ROUTE_DONE);

    assert(run(1,"192.168.50.0/24,10.0.0.0/8,2001:db8::/32,fd00::/8",0,0,
        "ip route replace 192.168.50.0/24 dev wrvpn2 table 20002\n"
        "ip route replace 10.0.0.0/8 dev wrvpn2 table 20002\n"
        "ip -6 route replace 2001:db8::/32 dev wrvpn2 table 20002\n"
        "ip -6 route replace fd00::/8 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n")
        ==WR_VPN_ROUTE_DONE);

    assert(run(1,"300.1.1.0/24",0,0,"")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"10.0.0.0/33",0,0,"")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"fd00::/129",0,0,"")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"2001:db8::/abc",0,0,"")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"10.0.0.0/8,",0,0,"")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"",0,0,"")==WR_VPN_ROUTE_EMPTY);

    /* An add failure rolls back every attempted route, including the failed
     * confirmed-success route. A rejected command is not deleted because the
     * route may have been owned by another process. */
    assert(run(1,"10.1.0.0/16, 10.2.0.0/16",1,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_FAILED);
    assert(run(1,"10.1.0.0/16, 2001:db8::/32",2,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route replace 2001:db8::/32 dev wrvpn2 table 20002\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_FAILED);

    /* Rule-install failures remove attempted family rules and all routes. */
    assert(run(1,"10.1.0.0/16",2,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_FAILED);
    assert(run(1,"10.1.0.0/16, ::/0",4,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route del ::/0 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_FAILED);
    assert(run(1,"10.1.0.0/16, ::/0",4,6,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route del ::/0 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_PARTIAL);
    unknown_at=2;
    assert(run(1,"10.1.0.0/16, ::/0",0,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_PARTIAL);
    unknown_at=0;
    present_at=3;
    assert(run(1,"10.1.0.0/16, ::/0",4,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 route del ::/0 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_FAILED);
    present_at=0;
    unknown_at=4;
    assert(run(1,"10.1.0.0/16, ::/0",0,0,
        "ip route replace 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route replace ::/0 dev wrvpn2 table 20002\n"
        "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_PARTIAL);
    unknown_at=0;

    /* Teardown attempts both rule families before deleting any routes and
     * continues through route deletion failures. */
    assert(run(0,"10.1.0.0/16, ::/0",0,0,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route del ::/0 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_DONE);
    assert(run(0,"10.1.0.0/16, ::/0",0,0,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.1.0.0/16 dev wrvpn2 table 20002\n"
        "ip -6 route del ::/0 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_DONE);
    assert(run(0,"10.1.0.0/16, ::/0",1,0,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 route del ::/0 dev wrvpn2 table 20002\n")
        ==WR_VPN_ROUTE_PARTIAL);

    memset(&resources,0,sizeof(resources));
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    recorded[0][0]=0;calls=0;fail_at=0;fail_at_second=0;
    assert(wr_vpn_rule_remove(&resources,&exec)==WR_VPN_ROUTE_DONE);
    assert(calls==2);
    assert(!strcmp(recorded[0],"ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003"));
    assert(!strcmp(recorded[1],"ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003"));

    puts("PASS VPN route apply: IPv4/IPv6 routes and rules, dual stack, complete preflight, family-scoped rollback and partial cleanup reporting");
    return 0;
}
