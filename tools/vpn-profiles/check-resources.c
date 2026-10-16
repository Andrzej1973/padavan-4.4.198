#include <assert.h>
#include <limits.h>
#include "resources.h"

int main(void)
{
    struct wr_vpn_resources a,b,changed,previous;
    unsigned int id=123, i,j;
    const char *bad[]={"","0","01","-1","+1"," 1","1 ","1\n","1/2","1000","4294967296","99999999999999999"};
    for (i=0;i<sizeof(bad)/sizeof(bad[0]);i++) {
        assert(!wr_vpn_profile_id(bad[i],&id)); assert(id==123);
    }
    assert(!wr_vpn_profile_id(NULL,&id));
    assert(!wr_vpn_profile_id("1",NULL));
    assert(wr_vpn_profile_id("999",&id) && id==999);
    assert(wr_vpn_resources_make(&a,1,WR_VPN_AMNEZIAWG));
    assert(wr_vpn_resources_make(&b,2,WR_VPN_WIREGUARD));
    assert(!strcmp(a.label,"AWG1") && !strcmp(b.label,"WG2"));
    assert(strcmp(a.interface,"wg0") && strcmp(a.interface,"wg1") && a.table!=51);
    assert(!wr_vpn_resources_conflict(&a,&b));
    previous=a;
    assert(!wr_vpn_resources_make(&a,0,WR_VPN_WIREGUARD));
    assert(!wr_vpn_resources_make(&a,UINT_MAX,WR_VPN_WIREGUARD));
    assert(!wr_vpn_resources_make(&a,1,(enum wr_vpn_protocol)9));
    assert(!memcmp(&a,&previous,sizeof(a)));
    assert(wr_vpn_resources_make(&changed,1,WR_VPN_WIREGUARD));
    assert(wr_vpn_resources_conflict(&a,&changed)); /* Same ID is one profile. */
    changed=b; changed.priority_tunnel=a.priority_main;
    assert(wr_vpn_resources_conflict(&a,&changed));
    changed=b; strcpy(changed.chain_mark,a.chain_remote);
    assert(wr_vpn_resources_conflict(&a,&changed));
    changed=b; strcpy(changed.dns,a.clients);
    assert(wr_vpn_resources_conflict(&a,&changed));
    for (i=1;i<=WR_VPN_PROFILE_ID_MAX;i++) {
        assert(wr_vpn_resources_make(&a,i,WR_VPN_WIREGUARD));
        assert(strlen(a.interface)<16 && strlen(a.chain_mark)<29 && strlen(a.clients)<32);
        assert(a.priority_main<a.priority_tunnel && a.priority_tunnel<32766);
        for (j=i+1;j<=WR_VPN_PROFILE_ID_MAX;j++) {
            assert(wr_vpn_resources_make(&b,j,WR_VPN_AMNEZIAWG));
            assert(!wr_vpn_resources_conflict(&a,&b));
        }
    }
    puts("PASS VPN profile resource model: stable IDs, WG/AWG coexistence namespaces, cross-resource conflicts; not runtime allocation or tunnel proof");
    return 0;
}
