#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "validate-process.h"
#include <net/if.h>
#include "link-observation.h"
#include "config-transaction.h"
#include "plan-report.h"
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
static int wr_observe(int root,unsigned int id)
{
    struct wr_vpn_record record;struct wr_vpn_resources resources;struct wr_vpn_link link;
    enum wr_vpn_store_result status=wr_vpn_store_get(root,id,&record);
    enum wr_vpn_link_result result;const char *kind;
    if (status==WR_VPN_STORE_NOT_FOUND) return 5;
    if (status==WR_VPN_STORE_BUSY) return 4;
    if (status!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    result=wr_vpn_link_query(resources.interface,&link);
    if (result!=WR_VPN_LINK_PRESENT) {
        printf("{\"id\":%u,\"interface_state\":\"%s\",\"ownership\":\"unverified\",\"up\":null}\n",
            id,result==WR_VPN_LINK_ABSENT?"absent":"unknown");
    } else {
        kind=!strcmp(link.kind,"wireguard")?"wireguard":!strcmp(link.kind,"amneziawg")?"amneziawg":"other";
        printf("{\"id\":%u,\"interface_state\":\"observed\",\"ownership\":\"unverified\",\"index\":%u,\"kind\":\"%s\",\"up\":%s}\n",
            id,link.index,kind,(link.flags&IFF_UP)?"true":"false");
    }
    return fflush(stdout)?3:0;
}
static const char *transaction_name(enum wr_vpn_transaction_result result)
{
    switch (result) {
    case WR_VPN_TRANSACTION_DONE: return "done";
    case WR_VPN_TRANSACTION_ABSENT: return "absent";
    case WR_VPN_TRANSACTION_BUSY: return "busy";
    case WR_VPN_TRANSACTION_STALE: return "stale";
    case WR_VPN_TRANSACTION_REFUSED: return "refused";
    case WR_VPN_TRANSACTION_UNKNOWN: return "unknown";
    case WR_VPN_TRANSACTION_MISMATCH: return "mismatch";
    case WR_VPN_TRANSACTION_ROLLBACK_FAILED: return "rollback-failed";
    case WR_VPN_TRANSACTION_IO: return "io";
    case WR_VPN_TRANSACTION_UNSAVED: return "unsaved";
    }
    return "invalid";
}
static int transaction_status(enum wr_vpn_transaction_result result)
{
    switch (result) {
    case WR_VPN_TRANSACTION_DONE: return 0;
    case WR_VPN_TRANSACTION_ABSENT: return 5;
    case WR_VPN_TRANSACTION_BUSY: return 4;
    case WR_VPN_TRANSACTION_STALE: return 7;
    case WR_VPN_TRANSACTION_REFUSED: return 2;
    case WR_VPN_TRANSACTION_UNKNOWN: return 6;
    case WR_VPN_TRANSACTION_MISMATCH: return 8;
    case WR_VPN_TRANSACTION_ROLLBACK_FAILED: return 9;
    case WR_VPN_TRANSACTION_IO: return 3;
    case WR_VPN_TRANSACTION_UNSAVED: return 10;
    }
    return 3;
}
/* Apply the stored protocol configuration to the interface the runtime session
 * already owns. Addresses, routes, DNS and connectivity remain controller work. */
static int wr_apply(int root,unsigned int id)
{
    struct wr_vpn_record record;struct wr_vpn_session expected;
    struct wr_vpn_resources resources;struct wr_vpn_runtime runtime={-1,-1};
    enum wr_vpn_store_result stored;enum wr_vpn_runtime_result status;
    enum wr_vpn_transaction_result result;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    if (wr_vpn_validate(record.protocol,record.config,record.size)!=WR_VPN_VALID) return 2;
    /* Read the session this call intends to act on; the transaction re-verifies
     * it under the operation lock, so a concurrent change becomes stale. */
    status=wr_vpn_runtime_lock(resources.runtime,&runtime);
    if (status!=WR_VPN_RUNTIME_OK) {
        printf("apply\t%u\t%s\n",id,status==WR_VPN_RUNTIME_BUSY?"busy":"io");
        return status==WR_VPN_RUNTIME_BUSY?4:3;
    }
    status=wr_vpn_runtime_read(&runtime,id,&expected);
    wr_vpn_runtime_unlock(&runtime);
    if (status!=WR_VPN_RUNTIME_OK) {
        printf("apply\t%u\tabsent\n",id);
        return 5;
    }
    result=wr_vpn_config_transaction(resources.runtime,&record,&expected,NULL);
    printf("apply\t%u\t%s\n",id,transaction_name(result));
    return fflush(stdout)?3:transaction_status(result);
}
/* Read-only preview: what would be applied, and what is observed now. */
static int wr_plan(int root,unsigned int id)
{
    struct wr_vpn_record record,snapshot;struct wr_vpn_session session;
    struct wr_vpn_resources resources;struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_session *observed=NULL;struct wr_vpn_record *rollback=NULL;
    enum wr_vpn_store_result stored;enum wr_vpn_runtime_result status;
    size_t capacity=2*WR_VPN_CONFIG_MAX+2048;char *text;int result=3;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    text=calloc(1,capacity);
    if (!text) return 3;
    status=wr_vpn_runtime_lock(resources.runtime,&runtime);
    if (status==WR_VPN_RUNTIME_OK) {
        if (wr_vpn_runtime_read(&runtime,id,&session)==WR_VPN_RUNTIME_OK) observed=&session;
        if (wr_vpn_runtime_snapshot_get(&runtime,id,&snapshot)==WR_VPN_RUNTIME_OK) rollback=&snapshot;
        wr_vpn_runtime_unlock(&runtime);
    }
    if (wr_vpn_plan_report(&record,observed,rollback,text,capacity)) {
        fputs(text,stdout);result=fflush(stdout)?3:0;
    }
    free(text);
    return result;
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
    } else if (argc==3 && (!strcmp(argv[1],"export") || !strcmp(argv[1],"observe") ||
                           !strcmp(argv[1],"apply") || !strcmp(argv[1],"plan"))) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
    } else if (!(argc==2 && !strcmp(argv[1],"list"))) return 2;
    if (mkdir(WR_VPN_STORE_ROOT,0700) && errno!=EEXIST) return 3;
    root=wr_vpn_store_open(WR_VPN_STORE_ROOT); if (root<0) return 3;
    if (!strcmp(argv[1],"create")) result=wr_create(root,id,protocol);
    else if (!strcmp(argv[1],"export")) result=wr_export(root,id);
    else if (!strcmp(argv[1],"observe")) result=wr_observe(root,id);
    else if (!strcmp(argv[1],"apply")) result=wr_apply(root,id);
    else if (!strcmp(argv[1],"plan")) result=wr_plan(root,id);
    else result=wr_list(root);
    close(root); return result;
}
