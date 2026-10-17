#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "addr-apply.h"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <string.h>

struct prefix {
    int family;
    unsigned char network[16];
    unsigned int bits;
    int valid;
};

static struct prefix parse_prefix(const char *text)
{
    struct prefix prefix;
    char buffer[64];const char *slash;size_t length;char *end;
    unsigned long bits,max;
    memset(&prefix,0,sizeof(prefix));
    if (!text) return prefix;
    slash=strchr(text,'/');
    length=slash?(size_t)(slash-text):strlen(text);
    if (!length || length>=sizeof(buffer)) return prefix;
    memcpy(buffer,text,length);buffer[length]=0;
    if (inet_pton(AF_INET,buffer,prefix.network)==1) {
        prefix.family=AF_INET;max=32;bits=32;
    } else if (inet_pton(AF_INET6,buffer,prefix.network)==1) {
        prefix.family=AF_INET6;max=128;bits=128;
    } else return prefix;
    if (slash) {
        bits=strtoul(slash+1,&end,10);
        if (*end || bits>max) return prefix;
    }
    prefix.bits=(unsigned int)bits;prefix.valid=1;
    return prefix;
}

/* Byte-wise comparison; prefixes of different families never overlap. */
static int overlaps(const struct prefix *a,const struct prefix *b)
{
    unsigned int shorter,full,rest;unsigned char mask;
    if (!a->valid || !b->valid || a->family!=b->family) return 0;
    shorter=a->bits<b->bits?a->bits:b->bits;
    full=shorter/8;rest=shorter%8;
    if (full && memcmp(a->network,b->network,full)) return 0;
    if (rest) {
        mask=(unsigned char)(0xffu<<(8-rest));
        if ((a->network[full]&mask)!=(b->network[full]&mask)) return 0;
    }
    return 1;
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
        if (!candidate.valid) return WR_VPN_ADDR_INVALID;
        if (add) {
            size_t i;
            for (i=0;i<protected_count;i++) {
                struct prefix protected_prefix=parse_prefix(protected_prefixes[i]);
                /* A malformed protected prefix must stop the start, not
                 * silently disappear from the LAN/management guard. */
                if (!protected_prefix.valid) return WR_VPN_ADDR_INVALID;
                if (overlaps(&candidate,&protected_prefix))
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
