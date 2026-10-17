#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "route-apply.h"
#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>

static int valid_prefix(const char *text,size_t length)
{
    char buffer[80],*slash,*end;size_t host_length;
    struct in_addr v4;struct in6_addr v6;unsigned long bits;
    if (!length || length>=sizeof(buffer)) return 0;
    memcpy(buffer,text,length);buffer[length]=0;
    slash=strchr(buffer,'/');
    host_length=slash?(size_t)(slash-buffer):strlen(buffer);
    if (!host_length || host_length>=sizeof(buffer)) return 0;
    if (slash) {
        char host[80];
        memcpy(host,buffer,host_length);host[host_length]=0;
        bits=strtoul(slash+1,&end,10);
        if (*end) return 0;
        if (inet_pton(AF_INET,host,&v4)==1) return bits<=32;
        if (inet_pton(AF_INET6,host,&v6)==1) return bits<=128;
        return 0;
    }
    return inet_pton(AF_INET,buffer,&v4)==1 || inet_pton(AF_INET6,buffer,&v6)==1;
}

/* Splits the comma-separated AllowedIPs value into validated prefixes. */
static int next_prefix(const char **cursor,char *out,size_t capacity)
{
    const char *comma;size_t length;
    while (*cursor && **cursor==' ') (*cursor)++;
    if (!*cursor || !**cursor) return 0;
    comma=strstr(*cursor,", ");
    length=comma?(size_t)(comma-*cursor):strlen(*cursor);
    while (length && (*cursor)[length-1]==' ') length--;
    if (!valid_prefix(*cursor,length) || length+1>capacity) return -1;
    memcpy(out,*cursor,length);out[length]=0;
    *cursor=comma?comma+2:NULL;
    return 1;
}

static int run_route(const struct wr_vpn_resources *resources,const char *prefix,
                     int add,const struct wr_vpn_exec *exec)
{
    char table[16];const char *argv[9];
    snprintf(table,sizeof(table),"%u",resources->table);
    argv[0]="ip";argv[1]="route";argv[2]=add?"replace":"del";argv[3]=prefix;
    argv[4]="dev";argv[5]=resources->interface;argv[6]="table";argv[7]=table;argv[8]=NULL;
    return exec->run(exec->context,argv);
}

static int run_rule(const struct wr_vpn_resources *resources,int add,
                    const struct wr_vpn_exec *exec)
{
    char mark[32],table[16],priority[16];const char *argv[11];
    snprintf(mark,sizeof(mark),"0x%08x/0xffffffff",resources->mark);
    snprintf(table,sizeof(table),"%u",resources->table);
    snprintf(priority,sizeof(priority),"%u",resources->priority_tunnel);
    argv[0]="ip";argv[1]="rule";argv[2]=add?"add":"del";argv[3]="fwmark";
    argv[4]=mark;argv[5]="lookup";argv[6]=table;argv[7]="priority";
    argv[8]=priority;argv[9]=NULL;
    return exec->run(exec->context,argv);
}

enum wr_vpn_route_result wr_vpn_routes_apply(const struct wr_vpn_resources *resources,
    const char *allowed_ips,int add,const struct wr_vpn_exec *exec)
{
    const char *cursor=allowed_ips;char prefix[80];int got;
    if (!resources || !allowed_ips || !exec || !exec->run) return WR_VPN_ROUTE_INVALID;
    if (!allowed_ips[0]) return WR_VPN_ROUTE_EMPTY;

    /* Validate every prefix before touching the system. */
    {
        const char *check=cursor;int seen=0;
        while ((got=next_prefix(&check,prefix,sizeof(prefix)))==1) seen++;
        if (got<0) return WR_VPN_ROUTE_INVALID;
        if (!seen) return WR_VPN_ROUTE_EMPTY;
    }

    if (!add && run_rule(resources,0,exec)) return WR_VPN_ROUTE_FAILED;
    while ((got=next_prefix(&cursor,prefix,sizeof(prefix)))==1) {
        if (run_route(resources,prefix,add,exec)) return WR_VPN_ROUTE_FAILED;
    }
    if (got<0) return WR_VPN_ROUTE_INVALID;
    if (add && run_rule(resources,1,exec)) return WR_VPN_ROUTE_FAILED;
    return WR_VPN_ROUTE_DONE;
}
