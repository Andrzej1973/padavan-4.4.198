#include "runtime-state.h"
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc,char **argv)
{
    struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_session intent,observed;
    struct wr_vpn_record record;
    unsigned long id;enum wr_vpn_protocol protocol;int store_root;
    enum wr_vpn_store_result stored;
    if (argc!=5) return 2;
    id=strtoul(argv[2],NULL,10);
    protocol=(enum wr_vpn_protocol)strtoul(argv[3],NULL,10);
    store_root=open(argv[1],O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (store_root<0) return 3;
    stored=wr_vpn_store_get(store_root,(unsigned int)id,&record);close(store_root);
    if (stored!=WR_VPN_STORE_OK || record.protocol!=protocol) return 4;
    if (!wr_vpn_session_new(&intent,(unsigned int)id,protocol,record.revision)) return 5;
    if (wr_vpn_runtime_lock(argv[4],&runtime)!=WR_VPN_RUNTIME_OK) return 6;
    if (wr_vpn_runtime_put(&runtime,&intent,NULL)!=WR_VPN_RUNTIME_OK) return 7;
    observed=intent;observed.index=73;
    if (wr_vpn_runtime_put(&runtime,&observed,&intent)!=WR_VPN_RUNTIME_OK) return 8;
    if (wr_vpn_runtime_snapshot_put(&runtime,&record)!=WR_VPN_RUNTIME_OK) return 9;
    wr_vpn_runtime_unlock(&runtime);
    return 0;
}
