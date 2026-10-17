#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "profile-apply.h"
#include <stdlib.h>
#include <string.h>

static void erase(void *data,size_t size)
{
    volatile unsigned char *p=data;while (size--) *p++=0;
}

int wr_vpn_profile_apply(const char *runtime_root,const struct wr_vpn_record *record,
    const struct wr_vpn_session *expected,const struct wr_vpn_apply_options *options,
    const struct wr_vpn_exec *exec,struct wr_vpn_apply_outcome *outcome)
{
    struct wr_vpn_config_plan *plan;
    enum wr_vpn_validation validation;
    if (!runtime_root || !record || !expected || !options || !exec || !outcome) return 0;
    memset(outcome,0,sizeof(*outcome));
    outcome->protocol=WR_VPN_TRANSACTION_REFUSED;
    outcome->addresses=WR_VPN_ADDR_EMPTY;
    outcome->routes=WR_VPN_ROUTE_EMPTY;
    outcome->dns=WR_VPN_DNS_EMPTY;
    plan=calloc(1,sizeof(*plan));
    if (!plan) return 0;
    validation=wr_vpn_prepare_config(record,plan);
    if (validation!=WR_VPN_VALID) goto done;

    /* Refuse before touching the protocol when addresses cannot be guarded. */
    if (plan->addresses[0] && (!options->protected_prefixes || !options->protected_count)) {
        outcome->addresses_attempted=1;
        outcome->addresses=WR_VPN_ADDR_INVALID;
        goto done;
    }

    outcome->protocol=wr_vpn_config_transaction(runtime_root,record,expected,NULL);
    if (outcome->protocol!=WR_VPN_TRANSACTION_DONE &&
        outcome->protocol!=WR_VPN_TRANSACTION_UNSAVED) goto done;

    if (plan->addresses[0]) {
        outcome->addresses_attempted=1;
        outcome->addresses=wr_vpn_addresses_apply(plan,1,options->protected_prefixes,
                                                  options->protected_count,exec);
        if (outcome->addresses!=WR_VPN_ADDR_DONE) goto done;
    }

    if (plan->allowed[0]) {
        outcome->routes_attempted=1;
        outcome->routes=wr_vpn_routes_apply(&plan->resources,plan->allowed,1,exec);
        if (outcome->routes!=WR_VPN_ROUTE_DONE) goto done;
    }

    /* DNS is a file for the opt-in dnsmasq step; a failure does not undo routes. */
    if (plan->dns[0]) {
        outcome->dns_attempted=1;
        outcome->dns=wr_vpn_dns_write(plan,runtime_root);
    }

done:
    erase(plan,sizeof(*plan));free(plan);
    return 1;
}
