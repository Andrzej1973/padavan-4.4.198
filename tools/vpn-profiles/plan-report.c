#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "plan-report.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void erase(void *data,size_t size)
{
    volatile unsigned char *p=data;while (size--) *p++=0;
}

static int add(char *out,size_t capacity,size_t *used,const char *format,...)
{
    va_list args;int n;char line[1200];
    va_start(args,format);n=vsnprintf(line,sizeof(line),format,args);va_end(args);
    if (n<0 || (size_t)n>=sizeof(line) || *used+(size_t)n+1>capacity) return 0;
    memcpy(out+*used,line,(size_t)n+1);*used+=(size_t)n;
    return 1;
}

/* One line per field: control characters would break the shape. */
static void single_line(char *text)
{
    for (; *text; text++) if ((unsigned char)*text<0x20) *text=' ';
}

int wr_vpn_plan_report(const struct wr_vpn_record *record,
    const struct wr_vpn_session *session,const struct wr_vpn_record *snapshot,
    char *out,size_t capacity)
{
    struct wr_vpn_config_plan *plan;enum wr_vpn_validation validation;
    const char *apply="ready";size_t used=0;int ok=1;
    if (!record || !out || capacity<128) return 0;
    plan=calloc(1,sizeof(*plan));
    if (!plan) return 0;
    validation=wr_vpn_prepare_config(record,plan);
    if (validation!=WR_VPN_VALID) {
        ok=add(out,capacity,&used,"id=%u\nprotocol=%s\nrevision=%llu\nbytes=%zu\n"
            "validation=%s\napply=invalid\n",record->id,
            record->protocol==WR_VPN_WIREGUARD?"wireguard":"amneziawg",
            (unsigned long long)record->revision,record->size,
            validation==WR_VPN_REJECTED?"rejected":"validator-failed");
        goto done;
    }
    single_line(plan->addresses);single_line(plan->dns);
    if (session && session->index && session->revision!=record->revision) apply="stale";
    else if (!session || !session->index) apply="no-session";
    else if (plan->hostname_endpoints) apply="needs-pinning";
    ok=add(out,capacity,&used,"id=%u\nprotocol=%s\nrevision=%llu\nbytes=%zu\n",
        record->id,record->protocol==WR_VPN_WIREGUARD?"wireguard":"amneziawg",
        (unsigned long long)record->revision,record->size) &&
       add(out,capacity,&used,"validation=valid\nendpoints=%s\n",
           plan->hostname_endpoints?"hostname":"numeric") &&
       add(out,capacity,&used,"addresses=%s\ndns=%s\n",plan->addresses,plan->dns) &&
       add(out,capacity,&used,"mtu=%u\n",plan->mtu);
    if (ok) {
        ok = session
            ? add(out,capacity,&used,"session=index=%u,revision=%llu\n",
                  session->index,(unsigned long long)session->revision)
            : add(out,capacity,&used,"session=absent\n");
    }
    if (ok) {
        ok = snapshot
            ? add(out,capacity,&used,"snapshot=revision=%llu\n",
                  (unsigned long long)snapshot->revision)
            : add(out,capacity,&used,"snapshot=absent\n");
    }
    if (ok) ok=add(out,capacity,&used,"apply=%s\n",apply);
done:
    erase(plan,sizeof(*plan));free(plan);
    return ok;
}
