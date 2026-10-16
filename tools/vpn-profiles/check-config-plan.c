#define _GNU_SOURCE
#include <assert.h>
#include <stdlib.h>
#include "config-plan.h"
int main(int argc,char **argv)
{
    struct wr_vpn_record record;struct wr_vpn_config_plan *plan,*before;
    enum wr_vpn_validation result;char mark[64];
    assert(argc==2);memset(&record,0,sizeof(record));record.id=2;record.revision=1;
    record.protocol=!strcmp(argv[1],"wireguard")?WR_VPN_WIREGUARD:WR_VPN_AMNEZIAWG;
    record.size=fread(record.config,1,sizeof(record.config),stdin);assert(!ferror(stdin));
    plan=malloc(sizeof(*plan));before=malloc(sizeof(*before));assert(plan && before);
    memset(plan,0xa5,sizeof(*plan));*before=*plan;
    result=wr_vpn_prepare_config(&record,plan);
    if (result!=WR_VPN_VALID) {
        assert(!memcmp(before,plan,sizeof(*plan)));free(before);free(plan);
        return result==WR_VPN_REJECTED?2:3;
    }
    assert(plan->resources.id==2 && !strcmp(plan->resources.interface,"wrvpn2"));
    snprintf(mark,sizeof(mark),"FwMark = %u\n",plan->resources.mark);
    assert(strstr(plan->native,mark) && strstr(plan->native,"PrivateKey = ") && strstr(plan->native,"PublicKey = "));
    assert(!strstr(plan->native,"Address = ") && !strstr(plan->native,"DNS = ") && !strstr(plan->native,"MTU = "));
    assert(!strcmp(plan->addresses,"10.8.0.2/32"));
    printf("{\"mtu\":%u,\"hostname_endpoints\":%s,\"dns_present\":%s}\n",plan->mtu,
        plan->hostname_endpoints?"true":"false",*plan->dns?"true":"false");
    free(before);free(plan);return 0;
}
