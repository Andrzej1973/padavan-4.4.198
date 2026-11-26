#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "teardown.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_CALLS 20
#define MAX_COMMAND 256
struct fixture { char commands[MAX_CALLS][MAX_COMMAND];int calls,fail_at,fail_at_second; };

static enum wr_vpn_exec_result record(void *context,const char *const argv[])
{
    struct fixture *f=context;size_t used=0;int i,call=++f->calls;
    assert(call<=MAX_CALLS);
    for (i=0;argv[i];i++) {
        int n=snprintf(f->commands[call-1]+used,MAX_COMMAND-used,"%s%s",i?" ":"",argv[i]);
        assert(n>=0 && (size_t)n<MAX_COMMAND-used);used+=(size_t)n;
    }
    return call==f->fail_at || call==f->fail_at_second;
}

static void setup(struct wr_vpn_config_plan *plan,struct wr_vpn_resources *resources)
{
    memset(plan,0,sizeof(*plan));memset(resources,0,sizeof(*resources));
    assert(wr_vpn_resources_make(resources,2,WR_VPN_WIREGUARD));
    plan->resources=*resources;
    strcpy(plan->addresses,"10.8.0.2/32");
    strcpy(plan->allowed,"10.0.0.0/8, 2001:db8::/32");
    strcpy(plan->dns,"1.1.1.1");
}

static void check_commands(const struct fixture *f,const char *expected)
{
    int i;const char *cursor=expected;
    for (i=0;i<f->calls;i++) {
        const char *end=strchr(cursor,'\n');size_t n;
        assert(end);n=(size_t)(end-cursor);
        assert(strlen(f->commands[i])==n && !memcmp(f->commands[i],cursor,n));
        cursor=end+1;
    }
    assert(!*cursor);
}

static int make_dns_dir(char *directory)
{
    struct wr_vpn_resources r;
    char file[512];FILE *fp;
    strcpy(directory,"/tmp/wrvpn-down-XXXXXX");assert(mkdtemp(directory));
    memset(&r,0,sizeof(r));assert(wr_vpn_resources_make(&r,2,WR_VPN_WIREGUARD));
    snprintf(file,sizeof(file),"%s/%s",directory,r.dns);
    fp=fopen(file,"w");assert(fp);fputs("1.1.1.1\n",fp);assert(!fclose(fp));
    return 1;
}

int main(void)
{
    struct wr_vpn_config_plan plan;struct wr_vpn_resources resources;
    struct wr_vpn_teardown_report report;struct fixture f;struct wr_vpn_exec exec={record,&f};
    char directory[64],file[512];
    const char *success_commands=
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.0.0.0/8 dev wrvpn2 table 20002\n"
        "ip -6 route del 2001:db8::/32 dev wrvpn2 table 20002\n"
        "ip address del 10.8.0.2/32 dev wrvpn2\n";
    setup(&plan,&resources);make_dns_dir(directory);
    snprintf(file,sizeof(file),"%s/%s",directory,resources.dns);
    memset(&f,0,sizeof(f));
    assert(wr_vpn_profile_cleanup(&plan,&resources,directory,1,&exec,&report)==WR_VPN_TEARDOWN_DONE);
    assert(report.routes==WR_VPN_ROUTE_DONE && report.addresses==WR_VPN_ADDR_DONE && report.dns==WR_VPN_DNS_DONE);
    check_commands(&f,success_commands);assert(access(file,F_OK)!=0);assert(!rmdir(directory));

    /* A failed rule deletion keeps that family's route and retains the DNS
     * file; the caller must retain the link/session for a retry. */
    setup(&plan,&resources);make_dns_dir(directory);snprintf(file,sizeof(file),"%s/%s",directory,resources.dns);
    memset(&f,0,sizeof(f));f.fail_at=1;
    assert(wr_vpn_profile_cleanup(&plan,&resources,directory,1,&exec,&report)==WR_VPN_TEARDOWN_PARTIAL);
    assert(report.routes==WR_VPN_ROUTE_PARTIAL && report.addresses==WR_VPN_ADDR_EMPTY && report.dns==WR_VPN_DNS_EMPTY);
    check_commands(&f,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 route del 2001:db8::/32 dev wrvpn2 table 20002\n");
    assert(!access(file,F_OK));unlink(file);assert(!rmdir(directory));

    /* Route cleanup failures are accumulated and prevent address, DNS and
     * interface teardown, while later routes still receive cleanup attempts. */
    setup(&plan,&resources);make_dns_dir(directory);snprintf(file,sizeof(file),"%s/%s",directory,resources.dns);
    memset(&f,0,sizeof(f));f.fail_at=3;
    assert(wr_vpn_profile_cleanup(&plan,&resources,directory,1,&exec,&report)==WR_VPN_TEARDOWN_PARTIAL);
    check_commands(&f,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip route del 10.0.0.0/8 dev wrvpn2 table 20002\n"
        "ip -6 route del 2001:db8::/32 dev wrvpn2 table 20002\n");
    assert(!access(file,F_OK));unlink(file);assert(!rmdir(directory));

    /* A failed address removal also keeps the link and per-profile DNS. */
    setup(&plan,&resources);make_dns_dir(directory);snprintf(file,sizeof(file),"%s/%s",directory,resources.dns);
    memset(&f,0,sizeof(f));f.fail_at=5;
    assert(wr_vpn_profile_cleanup(&plan,&resources,directory,1,&exec,&report)==WR_VPN_TEARDOWN_PARTIAL);
    check_commands(&f,success_commands);assert(!access(file,F_OK));unlink(file);assert(!rmdir(directory));

    /* DNS filesystem errors are reported instead of claiming a full stop. */
    setup(&plan,&resources);make_dns_dir(directory);snprintf(file,sizeof(file),"%s/%s",directory,resources.dns);
    assert(!unlink(file));assert(!mkdir(file,0700));memset(&f,0,sizeof(f));
    assert(wr_vpn_profile_cleanup(&plan,&resources,directory,1,&exec,&report)==WR_VPN_TEARDOWN_PARTIAL);
    assert(report.routes==WR_VPN_ROUTE_DONE && report.addresses==WR_VPN_ADDR_DONE && report.dns==WR_VPN_DNS_IO);
    check_commands(&f,success_commands);assert(!rmdir(file));assert(!rmdir(directory));

    /* Damaged config removes resource-derived rules and its DNS file but
     * leaves unknown routes/addresses and therefore reports UNKNOWN. */
    setup(&plan,&resources);make_dns_dir(directory);snprintf(file,sizeof(file),"%s/%s",directory,resources.dns);
    memset(&f,0,sizeof(f));
    assert(wr_vpn_profile_cleanup(&plan,&resources,directory,0,&exec,&report)==WR_VPN_TEARDOWN_UNKNOWN);
    check_commands(&f,
        "ip rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n"
        "ip -6 rule del fwmark 0x57560002/0xffffffff lookup 20002 priority 20003\n");
    assert(access(file,F_OK)!=0);assert(!rmdir(directory));

    puts("PASS VPN teardown: family policy before addresses/DNS, complete cleanup aggregation, retry context retained on partial/unknown state");
    return 0;
}
