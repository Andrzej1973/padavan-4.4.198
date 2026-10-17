#include "route-apply.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static char recorded[4096];
static int calls, fail_at;

static int record(void *context,const char *const argv[])
{
    int i;
    (void)context;
    calls++;
    if (fail_at==calls) return 1;
    for (i=0;argv[i];i++) { strcat(recorded,argv[i]);strcat(recorded," "); }
    strcat(recorded,"\n");
    return 0;
}

static const struct wr_vpn_exec exec={record,NULL};
static struct wr_vpn_resources resources;

static enum wr_vpn_route_result run(int add,const char *allowed,const char *expected)
{
    enum wr_vpn_route_result result;
    memset(&resources,0,sizeof(resources));
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    recorded[0]=0;calls=0;fail_at=0;
    result=wr_vpn_routes_apply(&resources,allowed,add,&exec);
    assert(!strcmp(recorded,expected));
    return result;
}

int main(void)
{
    assert(run(1,"0.0.0.0/0, ::/0",
               "ip route replace 0.0.0.0/0 dev wrvpn2 table 20002 \n"
               "ip route replace ::/0 dev wrvpn2 table 20002 \n"
               "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003 \n")
           ==WR_VPN_ROUTE_DONE);

    assert(run(1,"192.168.50.0/24",
               "ip route replace 192.168.50.0/24 dev wrvpn2 table 20002 \n"
               "ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003 \n")
           ==WR_VPN_ROUTE_DONE);

    /* Removal drops the rule first, then the table entries. */
    assert(run(0,"192.168.50.0/24",
               "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003 \n"
               "ip route del 192.168.50.0/24 dev wrvpn2 table 20002 \n")
           ==WR_VPN_ROUTE_DONE);

    assert(run(1,"", "")==WR_VPN_ROUTE_EMPTY);
    assert(run(1,"300.1.1.0/24","")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"10.0.0.0/33","")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"fd00::/129","")==WR_VPN_ROUTE_INVALID);
    assert(run(1,"not-a-prefix","")==WR_VPN_ROUTE_INVALID);

    memset(&resources,0,sizeof(resources));
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    recorded[0]=0;calls=0;fail_at=0;
    assert(wr_vpn_rule_remove(&resources,&exec)==WR_VPN_ROUTE_DONE);
    assert(!strcmp(recorded,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003 \n"));

    memset(&resources,0,sizeof(resources));
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    recorded[0]=0;calls=0;fail_at=2;
    assert(wr_vpn_routes_apply(&resources,"10.1.0.0/16, 10.2.0.0/16",1,&exec)==WR_VPN_ROUTE_FAILED);
    assert(!strcmp(recorded,"ip route replace 10.1.0.0/16 dev wrvpn2 table 20002 \n"));

    puts("PASS VPN route apply: profile table only, fwmark rule, rule removed first, "
         "prefix validation before any command and a runner failure stop");
    return 0;
}
