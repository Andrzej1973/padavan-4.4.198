#ifndef WR_VPN_IP_COMMAND_RESULT_H
#define WR_VPN_IP_COMMAND_RESULT_H
#include <string.h>
#include <stdio.h>
#include <stdint.h>

/* Input is the complete, successful output of a numeric rule listing
 * filtered by priority. Reject extra selectors or multiple matching rules. */
enum wr_vpn_rule_match { WR_VPN_RULE_ABSENT, WR_VPN_RULE_EXACT, WR_VPN_RULE_AMBIGUOUS };

static inline enum wr_vpn_rule_match wr_vpn_rule_match_listing(
    const char *listing, unsigned int priority, uint32_t mark, unsigned int table)
{
    char expected[128], explicit_mask[128];
    if (!listing) return WR_VPN_RULE_AMBIGUOUS;
    if (!*listing) return WR_VPN_RULE_ABSENT;
    snprintf(expected,sizeof(expected),"%u:\tfrom all fwmark 0x%x lookup %u\n",
             priority,(unsigned int)mark,table);
    snprintf(explicit_mask,sizeof(explicit_mask),
             "%u:\tfrom all fwmark 0x%x/0xffffffff lookup %u\n",
             priority,(unsigned int)mark,table);
    return (!strcmp(listing,expected) || !strcmp(listing,explicit_mask)) ?
           WR_VPN_RULE_EXACT : WR_VPN_RULE_AMBIGUOUS;
}

/* iproute2 reports an absent object using different errno text for routes,
 * rules and addresses. Accept only those deletion-specific cases as an
 * idempotent cleanup success; missing devices and all add failures remain. */
static inline int wr_vpn_ip_delete_absent(const char *const argv[],const char *error)
{
    int i=1;
    const char *object;
    if (!argv || !argv[0] || strcmp(argv[0],"ip") || !error) return 0;
    if (argv[i] && !strcmp(argv[i],"-6")) i++;
    object=argv[i];
    if (!object || !argv[i+1] || strcmp(argv[i+1],"del")) return 0;
    if (!strcmp(object,"route"))
        return strstr(error,"No such process") || strstr(error,"No such file or directory");
    if (!strcmp(object,"rule"))
        return strstr(error,"No such file or directory") || strstr(error,"No such process");
    if (!strcmp(object,"address") || !strcmp(object,"addr"))
        return strstr(error,"Cannot assign requested address") || strstr(error,"No such process");
    return 0;
}
#endif
