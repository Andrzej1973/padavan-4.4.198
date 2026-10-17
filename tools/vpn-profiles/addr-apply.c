#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "addr-apply.h"
#include <arpa/inet.h>
#include <string.h>

struct prefix {
    struct in_addr network;
    unsigned int bits;
    int valid;
};

static struct prefix parse_prefix(const char *text)
{
    struct prefix prefix;
    char buffer[64];const char *slash;size_t length;char *end;
    unsigned long bits;
    memset(&prefix,0,sizeof(prefix));
    slash=strchr(text,'/');
    length=slash?(size_t)(slash-text):strlen(text);
    if (!length || length>=sizeof(buffer)) return prefix;
    memcpy(buffer,text,length);buffer[length]=0;
    if (inet_pton(AF_INET,buffer,&prefix.network)!=1) return prefix;
    if (!slash) { prefix.bits=32;prefix.valid=1;return prefix; }
    bits=strtoul(slash+1,&end,10);
    if (*end || bits>32) return prefix;
    prefix.bits=(unsigned int)bits;prefix.valid=1;
    return prefix;
}

static unsigned int mask_of(unsigned int bits)
{
    return bits?(~0u)<<(32-bits):0u;
}

/* Either prefix contains the other's network address. */
static int overlaps(const struct prefix *a,const struct prefix *b)
{
    unsigned int shorter=a->bits<b->bits?a->bits:b->bits;
    unsigned int mask=mask_of(shorter);
    return (ntohl(a->network.s_addr)&mask)==(ntohl(b->network.s_addr)&mask);
}

static int address_text(const char *start,size_t length,char *out,size_t capacity)
{
    while (length && *start==' ') { start++;length--; }
    while (length && start[length-1]==' ') length--;
    if (!length || length+(size_t)1>capacity) return 0;
    memcpy(out,start,length);out[length]=0;
    return 1;
}

enum wr_vpn_addr_result wr_vpn_addresses_apply(const struct wr_vpn_config_plan *plan,
    int add,const char *const *protected_prefixes,size_t protected_count,
    const struct wr_vpn_exec *exec)
{
    const char *cursor;int any=0;
    if (!plan || !exec || !exec->run) return WR_VPN_ADDR_INVALID;
    if (protected_prefixes && protected_count>64) return WR_VPN_ADDR_INVALID;
    if (!plan->addresses[0]) return WR_VPN_ADDR_EMPTY;

    /* Validate every address and every overlap before running anything. */
    cursor=plan->addresses;
    while (cursor && *cursor) {
        const char *comma=strstr(cursor,", ");
        size_t length=comma?(size_t)(comma-cursor):strlen(cursor);
        char text[64];struct prefix candidate;
        if (!address_text(cursor,length,text,sizeof(text))) return WR_VPN_ADDR_INVALID;
        candidate=parse_prefix(text);
        if (!candidate.valid) {
            /* Not IPv4: accept a well-formed IPv6 prefix, reject anything else. */
            char buffer[64];struct in6_addr v6;const char *slash=strchr(text,'/');
            size_t host_length=slash?(size_t)(slash-text):strlen(text);
            unsigned long bits;
            char *end;
            if (!host_length || host_length>=sizeof(buffer)) return WR_VPN_ADDR_INVALID;
            memcpy(buffer,text,host_length);buffer[host_length]=0;
            if (inet_pton(AF_INET6,buffer,&v6)!=1) return WR_VPN_ADDR_INVALID;
            if (slash) {
                bits=strtoul(slash+1,&end,10);
                if (*end || bits>128) return WR_VPN_ADDR_INVALID;
            }
        } else if (add) {
            size_t i;
            for (i=0;i<protected_count;i++) {
                struct prefix protected_prefix=parse_prefix(protected_prefixes[i]);
                if (protected_prefix.valid && overlaps(&candidate,&protected_prefix))
                    return WR_VPN_ADDR_CONFLICT;
            }
        }
        any=1;
        cursor=comma?comma+2:NULL;
    }
    if (!any) return WR_VPN_ADDR_EMPTY;

    cursor=plan->addresses;
    while (cursor && *cursor) {
        const char *comma=strstr(cursor,", ");
        size_t length=comma?(size_t)(comma-cursor):strlen(cursor);
        char text[64];const char *argv[7];
        if (!address_text(cursor,length,text,sizeof(text))) return WR_VPN_ADDR_INVALID;
        argv[0]="ip";argv[1]="address";argv[2]=add?"add":"del";argv[3]=text;
        argv[4]="dev";argv[5]=plan->resources.interface;argv[6]=NULL;
        if (exec->run(exec->context,argv)) return WR_VPN_ADDR_FAILED;
        cursor=comma?comma+2:NULL;
    }
    return WR_VPN_ADDR_DONE;
}
