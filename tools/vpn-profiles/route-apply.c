#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "route-apply.h"
#include <arpa/inet.h>
#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int prefix_family(const char *text,size_t length)
{
    char buffer[80],address[80],*slash,*end;size_t host_length;
    struct in_addr v4;struct in6_addr v6;unsigned long bits;
    size_t i;
    if (!length || length>=sizeof(buffer)) return AF_UNSPEC;
    memcpy(buffer,text,length);buffer[length]=0;
    slash=strchr(buffer,'/');
    host_length=slash?(size_t)(slash-buffer):strlen(buffer);
    if (!host_length || host_length>=sizeof(address)) return AF_UNSPEC;
    memcpy(address,buffer,host_length);address[host_length]=0;
    if (inet_pton(AF_INET,address,&v4)==1) {
        if (!slash) return AF_INET;
        if (!slash[1]) return AF_UNSPEC;
        for (i=1;slash[i];i++) if (!isdigit((unsigned char)slash[i])) return AF_UNSPEC;
        errno=0;bits=strtoul(slash+1,&end,10);
        return !errno && !*end && bits<=32?AF_INET:AF_UNSPEC;
    }
    if (inet_pton(AF_INET6,address,&v6)==1) {
        if (!slash) return AF_INET6;
        if (!slash[1]) return AF_UNSPEC;
        for (i=1;slash[i];i++) if (!isdigit((unsigned char)slash[i])) return AF_UNSPEC;
        errno=0;bits=strtoul(slash+1,&end,10);
        return !errno && !*end && bits<=128?AF_INET6:AF_UNSPEC;
    }
    return AF_UNSPEC;
}

/* Splits AllowedIPs on commas, trims horizontal whitespace and validates the
 * whole token before returning it. Empty elements and trailing commas fail. */
static int next_prefix(const char **cursor,char *out,size_t capacity,int *family)
{
    const char *start,*comma;size_t length;
    if (!cursor || !*cursor || !**cursor) return 0;
    start=*cursor;comma=strchr(start,',');length=comma?(size_t)(comma-start):strlen(start);
    while (length && (start[0]==' ' || start[0]=='\t')) { start++;length--; }
    while (length && (start[length-1]==' ' || start[length-1]=='\t')) length--;
    if (!length || length>=capacity || (*family=prefix_family(start,length))==AF_UNSPEC)
        return -1;
    memcpy(out,start,length);out[length]=0;
    if (comma) {
        const char *next=comma+1;
        while (*next==' ' || *next=='\t') next++;
        if (!*next) return -1;
        *cursor=next;
    } else *cursor=NULL;
    return 1;
}

static int scan_prefixes(const char *allowed_ips,int *has4,int *has6,size_t *count)
{
    const char *cursor=allowed_ips;char prefix[80];int family,got;
    *has4=0;*has6=0;*count=0;
    while ((got=next_prefix(&cursor,prefix,sizeof(prefix),&family))==1) {
        if (family==AF_INET) *has4=1;
        else *has6=1;
        (*count)++;
    }
    return got<0?-1:(*count?1:0);
}

static enum wr_vpn_exec_result run_route(const struct wr_vpn_resources *resources,
                     const char *prefix,int family,int add,const struct wr_vpn_exec *exec)
{
    char table[16];const char *argv[10];int i=0;
    snprintf(table,sizeof(table),"%u",resources->table);
    argv[i++]="ip";
    if (family==AF_INET6) argv[i++]="-6";
    argv[i++]="route";argv[i++]=add?"replace":"del";argv[i++]=prefix;
    argv[i++]="dev";argv[i++]=resources->interface;argv[i++]="table";argv[i++]=table;argv[i]=NULL;
    return exec->run(exec->context,argv);
}

static enum wr_vpn_exec_result run_rule(const struct wr_vpn_resources *resources,
                    int family,int add,const struct wr_vpn_exec *exec)
{
    char mark[32],table[16],priority[16];const char *argv[12];int i=0;
    snprintf(mark,sizeof(mark),"0x%08x/0xffffffff",resources->mark);
    snprintf(table,sizeof(table),"%u",resources->table);
    snprintf(priority,sizeof(priority),"%u",resources->priority_tunnel);
    argv[i++]="ip";
    if (family==AF_INET6) argv[i++]="-6";
    argv[i++]="rule";argv[i++]=add?"add":"del";argv[i++]="fwmark";
    argv[i++]=mark;argv[i++]="lookup";argv[i++]=table;argv[i++]="priority";
    argv[i++]=priority;argv[i]=NULL;
    return exec->run(exec->context,argv);
}

static int remove_routes(const struct wr_vpn_resources *resources,const char *allowed_ips,
                         int only_family,size_t limit,const struct wr_vpn_exec *exec)
{
    const char *cursor=allowed_ips;char prefix[80];int family,got,failed=0;size_t index=0;
    while ((got=next_prefix(&cursor,prefix,sizeof(prefix),&family))==1) {
        index++;
        if ((limit==(size_t)-1 || index<=limit) && (!only_family || family==only_family) &&
            run_route(resources,prefix,family,0,exec)!=WR_VPN_EXEC_DONE) failed=1;
    }
    if (got<0) failed=1;
    return failed;
}

enum wr_vpn_route_result wr_vpn_routes_apply(const struct wr_vpn_resources *resources,
    const char *allowed_ips,int add,const struct wr_vpn_exec *exec)
{
    const char *cursor;char prefix[80];int has4,has6,family,got,failed=0;
    enum wr_vpn_exec_result route_result,rule4_result=WR_VPN_EXEC_FAILED;
    enum wr_vpn_exec_result rule6_result=WR_VPN_EXEC_FAILED,remove_result;
    int cleanup_failed,can_remove4,can_remove6;
    size_t count,succeeded=0;
    if (!resources || !allowed_ips || !exec || !exec->run) return WR_VPN_ROUTE_INVALID;
    if (!allowed_ips[0]) return WR_VPN_ROUTE_EMPTY;
    if (scan_prefixes(allowed_ips,&has4,&has6,&count)<0) return WR_VPN_ROUTE_INVALID;
    if (add) {
        cursor=allowed_ips;
        while ((got=next_prefix(&cursor,prefix,sizeof(prefix),&family))==1) {
            route_result=run_route(resources,prefix,family,1,exec);
            if (route_result!=WR_VPN_EXEC_DONE) {
                cleanup_failed=remove_routes(resources,allowed_ips,0,succeeded,exec);
                return cleanup_failed || route_result==WR_VPN_EXEC_UNKNOWN?
                       WR_VPN_ROUTE_PARTIAL:WR_VPN_ROUTE_FAILED;
            }
            succeeded++;
        }
        if (got<0) return WR_VPN_ROUTE_INVALID;
        if (has4) rule4_result=run_rule(resources,AF_INET,1,exec);
        if ((!has4 || rule4_result==WR_VPN_EXEC_DONE || rule4_result==WR_VPN_EXEC_PRESENT) && has6)
            rule6_result=run_rule(resources,AF_INET6,1,exec);
        if ((!has4 || rule4_result==WR_VPN_EXEC_DONE || rule4_result==WR_VPN_EXEC_PRESENT) &&
            (!has6 || rule6_result==WR_VPN_EXEC_DONE || rule6_result==WR_VPN_EXEC_PRESENT))
            return WR_VPN_ROUTE_DONE;

        /* Remove only rules this attempt confirmed it installed. If dispatch
         * timed out, preserve that family's routes because the rule's state
         * is unknown. A definite EEXIST/rejection is never followed by a
         * delete that could remove a rule owned by another process. */
        cleanup_failed=0;
        can_remove4=!has4 || rule4_result==WR_VPN_EXEC_FAILED;
        can_remove6=!has6 || rule6_result==WR_VPN_EXEC_FAILED;
        if (has4 && rule4_result==WR_VPN_EXEC_DONE) {
            remove_result=run_rule(resources,AF_INET,0,exec);
            can_remove4=remove_result==WR_VPN_EXEC_DONE;
            if (!can_remove4) cleanup_failed=1;
        } else if (rule4_result==WR_VPN_EXEC_UNKNOWN) {
            can_remove4=0;cleanup_failed=1;
        }
        if (has6 && rule6_result==WR_VPN_EXEC_DONE) {
            remove_result=run_rule(resources,AF_INET6,0,exec);
            can_remove6=remove_result==WR_VPN_EXEC_DONE;
            if (!can_remove6) cleanup_failed=1;
        } else if (rule6_result==WR_VPN_EXEC_UNKNOWN) {
            can_remove6=0;cleanup_failed=1;
        }
        if (can_remove4 && remove_routes(resources,allowed_ips,AF_INET,(size_t)-1,exec)) cleanup_failed=1;
        if (can_remove6 && remove_routes(resources,allowed_ips,AF_INET6,(size_t)-1,exec)) cleanup_failed=1;
        if (rule4_result==WR_VPN_EXEC_UNKNOWN || rule6_result==WR_VPN_EXEC_UNKNOWN)
            return WR_VPN_ROUTE_PARTIAL;
        return cleanup_failed?WR_VPN_ROUTE_PARTIAL:WR_VPN_ROUTE_FAILED;
    }

    /* Stop redirecting each family before deleting that family's routes.
     * Continue cleanup after individual failures, but retain routes wherever
     * their marked rule could still be active. */
    rule4_result=run_rule(resources,AF_INET,0,exec);
    rule6_result=run_rule(resources,AF_INET6,0,exec);
    if (has4 && rule4_result==WR_VPN_EXEC_DONE && remove_routes(resources,allowed_ips,AF_INET,(size_t)-1,exec)) failed=1;
    if (has6 && rule6_result==WR_VPN_EXEC_DONE && remove_routes(resources,allowed_ips,AF_INET6,(size_t)-1,exec)) failed=1;
    if (rule4_result!=WR_VPN_EXEC_DONE || rule6_result!=WR_VPN_EXEC_DONE) failed=1;
    return failed?WR_VPN_ROUTE_PARTIAL:WR_VPN_ROUTE_DONE;
}

enum wr_vpn_route_result wr_vpn_rule_remove(const struct wr_vpn_resources *resources,
                                            const struct wr_vpn_exec *exec)
{
    int failed=0;
    if (!resources || !exec || !exec->run) return WR_VPN_ROUTE_INVALID;
    if (run_rule(resources,AF_INET,0,exec)!=WR_VPN_EXEC_DONE) failed=1;
    if (run_rule(resources,AF_INET6,0,exec)!=WR_VPN_EXEC_DONE) failed=1;
    return failed?WR_VPN_ROUTE_PARTIAL:WR_VPN_ROUTE_DONE;
}
