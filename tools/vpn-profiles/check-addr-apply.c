#include "addr-apply.h"
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

static struct wr_vpn_config_plan plan;
static const struct wr_vpn_exec exec={record,NULL};
static const char *protected_prefixes[]={"192.168.20.0/24","172.16.0.0/12"};

static enum wr_vpn_addr_result run_list(int add,const char *addresses,
    const char *const *protected_list,size_t protected_len,const char *expected)
{
    enum wr_vpn_addr_result result;
    memset(&plan,0,sizeof(plan));
    plan.resources.id=2;plan.resources.protocol=WR_VPN_WIREGUARD;
    snprintf(plan.resources.interface,sizeof(plan.resources.interface),"wrvpn2");
    snprintf(plan.addresses,sizeof(plan.addresses),"%s",addresses);
    recorded[0]=0;calls=0;fail_at=0;
    result=wr_vpn_addresses_apply(&plan,add,protected_list,protected_len,&exec);
    assert(!strcmp(recorded,expected));
    return result;
}
static enum wr_vpn_addr_result run(int add,const char *addresses,const char *expected)
{
    return run_list(add,addresses,protected_prefixes,
                    sizeof(protected_prefixes)/sizeof(protected_prefixes[0]),expected);
}

int main(void)
{
    assert(run(1,"10.8.0.2/32, fd00::2/128",
               "ip address add 10.8.0.2/32 dev wrvpn2 \n"
               "ip address add fd00::2/128 dev wrvpn2 \n")==WR_VPN_ADDR_DONE);

    assert(run(0,"10.8.0.2/32",
               "ip address del 10.8.0.2/32 dev wrvpn2 \n")==WR_VPN_ADDR_DONE);

    assert(run(1,"", "")==WR_VPN_ADDR_EMPTY);

    assert(run(1,"300.1.1.1/32","")==WR_VPN_ADDR_INVALID);
    assert(run(1,"fd00::2/129","")==WR_VPN_ADDR_INVALID);
    assert(run(1,"not-an-address","")==WR_VPN_ADDR_INVALID);

    /* A connected route for a protected prefix could move the router's traffic. */
    assert(run(1,"192.168.20.5/32","")==WR_VPN_ADDR_CONFLICT);
    assert(run(1,"192.168.0.0/16","")==WR_VPN_ADDR_CONFLICT);
    assert(run(1,"172.20.1.1/32","")==WR_VPN_ADDR_CONFLICT);

    /* Deletion of an address inside a protected prefix is not requested here. */
    assert(run(0,"192.168.20.5/32",
               "ip address del 192.168.20.5/32 dev wrvpn2 \n")==WR_VPN_ADDR_DONE);

    memset(&plan,0,sizeof(plan));
    plan.resources.id=2;plan.resources.protocol=WR_VPN_WIREGUARD;
    snprintf(plan.resources.interface,sizeof(plan.resources.interface),"wrvpn2");
    snprintf(plan.addresses,sizeof(plan.addresses),"%s","10.8.0.2/32, 10.8.0.3/32");
    recorded[0]=0;calls=0;fail_at=2;
    assert(wr_vpn_addresses_apply(&plan,1,protected_prefixes,2,&exec)==WR_VPN_ADDR_FAILED);
    assert(!strcmp(recorded,"ip address add 10.8.0.2/32 dev wrvpn2 \n"));

    /* IPv6 addresses are guarded by IPv6 protected prefixes as well. */
    {
        static const char *protected_v6[]={"fd00::/64"};
        assert(run_list(1,"fd00::2/128",protected_v6,1,"")==WR_VPN_ADDR_CONFLICT);
        assert(run_list(1,"fd00::/48",protected_v6,1,"")==WR_VPN_ADDR_CONFLICT);
        assert(run_list(1,"fd00:1::2/64",protected_v6,1,
            "ip address add fd00:1::2/64 dev wrvpn2 \n")==WR_VPN_ADDR_DONE);
    }
    /* A malformed protected prefix refuses everything instead of vanishing. */
    {
        static const char *protected_bad[]={"not-a-prefix"};
        assert(run_list(1,"10.8.0.2/32",protected_bad,1,"")==WR_VPN_ADDR_INVALID);
    }

    puts("PASS VPN address apply: exact argv, IPv4/IPv6 validation, IPv4 and IPv6 "
         "protected-prefix refusal before any command, malformed guard refusal, "
         "and a runner failure stop");
    return 0;
}
