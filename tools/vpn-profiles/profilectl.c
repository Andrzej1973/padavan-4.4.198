#define _GNU_SOURCE
#include "validate-process.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

#ifndef WR_VPN_STORE_ROOT
#define WR_VPN_STORE_ROOT "/etc/storage/wrvpn"
#endif

/* Initial management surface: validated create, metadata list, explicit
 * private export. No network actions, edits, deletion or NVRAM migration.
 * Those require the shared lifecycle lock and observed ownership first.
 */
static int wr_create(int root,unsigned int id,enum wr_vpn_protocol protocol)
{
    unsigned char data[WR_VPN_CONFIG_MAX+1];
    size_t size=fread(data,1,sizeof(data),stdin); uint64_t revision;
    enum wr_vpn_store_result result;
    enum wr_vpn_validation validation;
    if (ferror(stdin) || !size || size>WR_VPN_CONFIG_MAX) return 2;
    validation=wr_vpn_validate(protocol,data,size);
    if (validation!=WR_VPN_VALID) return validation==WR_VPN_REJECTED?2:3;
    result=wr_vpn_store_put(root,id,protocol,data,size,0,&revision);
    if (result==WR_VPN_STORE_EXISTS) return 5;
    if (result==WR_VPN_STORE_BUSY) return 4;
    if (result!=WR_VPN_STORE_OK && result!=WR_VPN_STORE_COMMITTED_UNSYNCED) return 3;
    printf("saved\t%u\t%llu%s\n",id,(unsigned long long)revision,
           result==WR_VPN_STORE_COMMITTED_UNSYNCED?"\tsync-unconfirmed":"");
    return result==WR_VPN_STORE_OK?0:6;
}
static int wr_export(int root,unsigned int id)
{
    struct wr_vpn_record record;
    enum wr_vpn_store_result result=wr_vpn_store_get(root,id,&record);
    if (result==WR_VPN_STORE_NOT_FOUND) return 5;
    if (result==WR_VPN_STORE_BUSY) return 4;
    if (result!=WR_VPN_STORE_OK || wr_vpn_validate(record.protocol,record.config,record.size)!=WR_VPN_VALID) return 3;
    return fwrite(record.config,1,record.size,stdout)==record.size && !fflush(stdout)?0:3;
}
static int wr_list(int root)
{
    DIR *dir=fdopendir(openat(root,".",O_RDONLY|O_DIRECTORY|O_CLOEXEC));
    struct dirent *entry;
    int result=0;
    if (!dir) return 3;
    /* Per-row coherent metadata, not a global runtime/status snapshot. */
    for (;;) {
        unsigned int id; struct wr_vpn_record record;
        struct wr_vpn_resources resources;
        enum wr_vpn_store_result status;
        errno=0; entry=readdir(dir);
        if (!entry) { if (errno) result=3; break; }
        if (!strcmp(entry->d_name,".") || !strcmp(entry->d_name,"..") ||
            !strcmp(entry->d_name,".lock") || !strncmp(entry->d_name,".new-",5)) continue;
        if (!wr_vpn_profile_id(entry->d_name,&id)) { result=3; break; }
        status=wr_vpn_store_get(root,id,&record);
        if (status==WR_VPN_STORE_NOT_FOUND) continue;
        if (status!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) { result=3; break; }
        printf("%u\t%s\t%llu\n",id,resources.label,(unsigned long long)record.revision);
    }
    closedir(dir);
    return result?result:(fflush(stdout)?3:0);
}
int main(int argc,char **argv)
{
    unsigned int id=0; int root,result;
    enum wr_vpn_protocol protocol=WR_VPN_WIREGUARD;
    umask(077);
    if (signal(SIGCHLD,SIG_DFL)==SIG_ERR) return 3;
    if (argc==4 && !strcmp(argv[1],"create")) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
        if (!strcmp(argv[3],"amneziawg")) protocol=WR_VPN_AMNEZIAWG;
        else if (strcmp(argv[3],"wireguard")) return 2;
    } else if (argc==3 && !strcmp(argv[1],"export")) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
    } else if (!(argc==2 && !strcmp(argv[1],"list"))) return 2;
    if (mkdir(WR_VPN_STORE_ROOT,0700) && errno!=EEXIST) return 3;
    root=wr_vpn_store_open(WR_VPN_STORE_ROOT); if (root<0) return 3;
    if (!strcmp(argv[1],"create")) result=wr_create(root,id,protocol);
    else if (!strcmp(argv[1],"export")) result=wr_export(root,id);
    else result=wr_list(root);
    close(root); return result;
}
