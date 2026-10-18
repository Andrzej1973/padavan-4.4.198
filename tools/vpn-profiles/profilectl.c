#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "validate-process.h"
#include <net/if.h>
#include "link-observation.h"
#include "config-transaction.h"
#include "plan-report.h"
#include "profile-apply.h"
#include "link-lifecycle.h"
#include "protect.h"
#include "endpoint-pin.h"
#include <arpa/inet.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <poll.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
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
enum profile_state { PROFILE_IDLE, PROFILE_LIVE, PROFILE_BUSY, PROFILE_UNKNOWN };
/* Never create runtime state just to inspect whether a profile is idle. */
static enum profile_state profile_state(const struct wr_vpn_resources *resources)
{
    struct wr_vpn_runtime runtime={-1,-1};struct wr_vpn_session session;
    struct stat st;enum wr_vpn_runtime_result status;
    if (lstat(resources->runtime,&st)) return errno==ENOENT?PROFILE_IDLE:PROFILE_UNKNOWN;
    if (!S_ISDIR(st.st_mode)) return PROFILE_UNKNOWN;
    status=wr_vpn_runtime_lock(resources->runtime,&runtime);
    if (status==WR_VPN_RUNTIME_BUSY) return PROFILE_BUSY;
    if (status!=WR_VPN_RUNTIME_OK) return PROFILE_UNKNOWN;
    status=wr_vpn_runtime_read(&runtime,resources->id,&session);
    wr_vpn_runtime_unlock(&runtime);
    if (status==WR_VPN_RUNTIME_ABSENT) return PROFILE_IDLE;
    return status==WR_VPN_RUNTIME_OK?PROFILE_LIVE:PROFILE_UNKNOWN;
}
/* Stop and delete are distinct actions: a live profile must be brought down
 * before its record becomes a tombstone, or its link would be orphaned. */
static int wr_delete(int root,unsigned int id)
{
    struct wr_vpn_record record;struct wr_vpn_resources resources;
    enum wr_vpn_store_result stored;uint64_t revision;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    switch (profile_state(&resources)) {
    case PROFILE_IDLE: break;
    case PROFILE_LIVE: printf("delete\t%u\tlive\n",id); return 4;
    case PROFILE_BUSY: printf("delete\t%u\tbusy\n",id); return 4;
    default: return 3;
    }
    stored=wr_vpn_store_delete(root,id,record.revision,&revision);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored==WR_VPN_STORE_BUSY) return 4;
    if (stored!=WR_VPN_STORE_OK && stored!=WR_VPN_STORE_COMMITTED_UNSYNCED) return 3;
    printf("deleted\t%u\t%llu%s\n",id,(unsigned long long)revision,
           stored==WR_VPN_STORE_COMMITTED_UNSYNCED?"\tsync-unconfirmed":"");
    return stored==WR_VPN_STORE_OK?0:6;
}
/* Replace the stored configuration only while the profile is stopped: a live
 * session keeps the revision it was created for, so it must be brought down
 * and up again to run the edited record. */
static int wr_edit(int root,unsigned int id,uint64_t expected)
{
    struct wr_vpn_record record;struct wr_vpn_resources resources;
    unsigned char data[WR_VPN_CONFIG_MAX+1];size_t size;
    enum wr_vpn_store_result stored;uint64_t revision;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    if (expected && record.revision!=expected) return 7;
    size=fread(data,1,sizeof(data),stdin);
    if (ferror(stdin) || !size || size>WR_VPN_CONFIG_MAX) return 2;
    if (wr_vpn_validate(record.protocol,data,size)!=WR_VPN_VALID) return 2;
    switch (profile_state(&resources)) {
    case PROFILE_IDLE: break;
    case PROFILE_LIVE: printf("edit\t%u\tlive\n",id); return 4;
    case PROFILE_BUSY: printf("edit\t%u\tbusy\n",id); return 4;
    default: return 3;
    }
    stored=wr_vpn_store_put(root,id,record.protocol,data,size,record.revision,&revision);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored==WR_VPN_STORE_STALE) return 7;
    if (stored==WR_VPN_STORE_BUSY) return 4;
    if (stored!=WR_VPN_STORE_OK && stored!=WR_VPN_STORE_COMMITTED_UNSYNCED) return 3;
    printf("saved\t%u\t%llu%s\n",id,(unsigned long long)revision,
           stored==WR_VPN_STORE_COMMITTED_UNSYNCED?"\tsync-unconfirmed":"");
    return stored==WR_VPN_STORE_OK?0:6;
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
/* Real command runner: ip only, no shell, short timeout. */
static long long elapsed_ms(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) return -1;
    return (long long)now.tv_sec*1000+now.tv_nsec/1000000;
}
static int run_ip(void *context,const char *const argv[])
{
    char *const env[]={"LC_ALL=C",NULL};
    pid_t child,done;int status;long long began;
    (void)context;
    child=fork();
    if (child<0) return 1;
    if (!child) {
        execve("/sbin/ip",(char *const *)argv,env);
        execve("/bin/ip",(char *const *)argv,env);
        _exit(127);
    }
    began=elapsed_ms();
    for (;;) {
        done=waitpid(child,&status,WNOHANG);
        if (done==child) return (WIFEXITED(status) && WEXITSTATUS(status)==0)?0:1;
        if (done<0 && errno!=EINTR) return 1;
        if (began<0 || elapsed_ms()-began>3000) {
            kill(child,SIGKILL);
            while (waitpid(child,&status,0)<0 && errno==EINTR) {}
            return 1;
        }
        (void)poll(NULL,0,20);
    }
}
static const char *address_name(enum wr_vpn_addr_result result)
{
    switch (result) {
    case WR_VPN_ADDR_DONE: return "done";
    case WR_VPN_ADDR_EMPTY: return "empty";
    case WR_VPN_ADDR_INVALID: return "invalid";
    case WR_VPN_ADDR_CONFLICT: return "conflict";
    case WR_VPN_ADDR_FAILED: return "failed";
    }
    return "invalid";
}
static const char *route_name(enum wr_vpn_route_result result)
{
    switch (result) {
    case WR_VPN_ROUTE_DONE: return "done";
    case WR_VPN_ROUTE_EMPTY: return "empty";
    case WR_VPN_ROUTE_INVALID: return "invalid";
    case WR_VPN_ROUTE_FAILED: return "failed";
    }
    return "invalid";
}
static const char *dns_name(enum wr_vpn_dns_result result)
{
    switch (result) {
    case WR_VPN_DNS_DONE: return "done";
    case WR_VPN_DNS_EMPTY: return "empty";
    case WR_VPN_DNS_INVALID: return "invalid";
    case WR_VPN_DNS_IO: return "io";
    }
    return "invalid";
}
static const char *lifecycle_name(enum wr_vpn_lifecycle_result result)
{
    switch (result) {
    case WR_VPN_LIFECYCLE_OK: return "ok";
    case WR_VPN_LIFECYCLE_BUSY: return "busy";
    case WR_VPN_LIFECYCLE_REFUSED: return "refused";
    case WR_VPN_LIFECYCLE_UNKNOWN: return "unknown";
    }
    return "unknown";
}
/* A failed `up` must not leave an owned link or a stale fwmark rule. Routes
 * and addresses live on the device and disappear with it; the rule does not. */
static const char *release_name(int released)
{
    return released==0?"done":released<0?"unknown":"failed";
}
/* System resolver used only while no tunnel route exists (before acquire). */
static int resolve_host(const char *host,char *numeric,size_t capacity)
{
    struct addrinfo hints,*list=NULL,*item;int rc;const char *text=NULL;
    memset(&hints,0,sizeof(hints));
    hints.ai_family=AF_UNSPEC;
    hints.ai_socktype=SOCK_DGRAM;
    hints.ai_flags=AI_ADDRCONFIG;
    rc=getaddrinfo(host,NULL,&hints,&list);
    if (rc) return 0;
    for (item=list;item;item=item->ai_next) {
        if (item->ai_family==AF_INET) {
            text=inet_ntop(AF_INET,&((struct sockaddr_in *)item->ai_addr)->sin_addr,
                           numeric,capacity);
            break;
        }
        if (item->ai_family==AF_INET6 && !text) {
            text=inet_ntop(AF_INET6,&((struct sockaddr_in6 *)item->ai_addr)->sin6_addr,
                           numeric,capacity);
        }
    }
    freeaddrinfo(list);
    return text!=NULL;
}
/* Pin hostnames into a copy for this activation; the store keeps the name. */
static int pin_record(const struct wr_vpn_record *input,struct wr_vpn_record *output)
{
    switch (wr_vpn_pin_endpoints(input,resolve_host,output)) {
    case WR_VPN_PIN_DONE:
    case WR_VPN_PIN_UNCHANGED: return 1;
    case WR_VPN_PIN_UNRESOLVED: return 0;
    default: return -1;
    }
}
static int release_failed_up(const struct wr_vpn_resources *resources,
                             const struct wr_vpn_session *expected)
{
    struct wr_vpn_exec exec={run_ip,NULL};
    struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_session current;
    enum wr_vpn_runtime_result status;
    enum wr_vpn_lifecycle_result down;
    status=wr_vpn_runtime_lock(resources->runtime,&runtime);
    if (status!=WR_VPN_RUNTIME_OK) return -1;
    status=wr_vpn_runtime_read(&runtime,resources->id,&current);
    /* Another session may have replaced ours while the transport ran. Its
     * rule and link belong to it, so leave both alone. */
    if (status!=WR_VPN_RUNTIME_OK ||
        current.id!=expected->id || current.protocol!=expected->protocol ||
        current.revision!=expected->revision || current.index!=expected->index ||
        memcmp(current.nonce,expected->nonce,sizeof(current.nonce))) {
        wr_vpn_runtime_unlock(&runtime);
        return -1;
    }
    (void)wr_vpn_rule_remove(resources,&exec);
    down=wr_vpn_link_release(&runtime,resources->id,&wr_vpn_system_links);
    wr_vpn_runtime_unlock(&runtime);
    return down==WR_VPN_LIFECYCLE_OK?0:1;
}
/* Create the owned link, then apply configuration, addresses and routes. */
static int wr_up(int root,unsigned int id,const char *protect)
{
    struct wr_vpn_record record;struct wr_vpn_session session;
    struct wr_vpn_resources resources;struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_apply_options options={NULL,0};struct wr_vpn_apply_outcome outcome;
    struct wr_vpn_exec exec={run_ip,NULL};
    enum wr_vpn_store_result stored;enum wr_vpn_runtime_result status;
    enum wr_vpn_lifecycle_result up;int result=0,released;
    char buffer[256];const char *prefixes[8];int count=0;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    if (wr_vpn_validate(record.protocol,record.config,record.size)!=WR_VPN_VALID) return 2;
    if (protect && *protect) {
        count=wr_vpn_parse_protect(protect,buffer,sizeof(buffer),prefixes,8);
        if (count<0) return 2;
        options.protected_prefixes=prefixes;options.protected_count=(size_t)count;
    }
    /* Resolve before the link exists, so the answer cannot use its routes. */
    {
        struct wr_vpn_record pinned;int pin=pin_record(&record,&pinned);
        if (pin<0) { printf("up\t%u\tendpoint=invalid\n",id); return 2; }
        if (!pin) { printf("up\t%u\tendpoint=unresolved\n",id); return 2; }
        record=pinned;
    }
    status=wr_vpn_runtime_lock(resources.runtime,&runtime);
    if (status!=WR_VPN_RUNTIME_OK) {
        printf("up\t%u\t%s\n",id,status==WR_VPN_RUNTIME_BUSY?"busy":"io");
        return status==WR_VPN_RUNTIME_BUSY?4:3;
    }
    up=wr_vpn_link_acquire(&runtime,id,record.protocol,record.revision,
                           &wr_vpn_system_links,&session);
    wr_vpn_runtime_unlock(&runtime);
    if (up!=WR_VPN_LIFECYCLE_OK) {
        printf("up\t%u\t%s\n",id,lifecycle_name(up));
        return 6;
    }
    if (!wr_vpn_profile_apply(resources.runtime,&record,&session,&options,&exec,&outcome)) {
        released=release_failed_up(&resources,&session);
        printf("up\t%u\tapply=refused\tcleanup=%s\n",id,release_name(released));
        return 3;
    }
    printf("up\t%u\tprotocol=%s\taddresses=%s\troutes=%s\tdns=%s\n",id,
           transaction_name(outcome.protocol),address_name(outcome.addresses),
           route_name(outcome.routes),dns_name(outcome.dns));
    if (fflush(stdout)) return 3;
    if (outcome.addresses_attempted && outcome.addresses!=WR_VPN_ADDR_DONE) result=8;
    else if (outcome.protocol!=WR_VPN_TRANSACTION_DONE &&
        outcome.protocol!=WR_VPN_TRANSACTION_UNSAVED)
        result=transaction_status(outcome.protocol);
    else if (outcome.routes_attempted && outcome.routes!=WR_VPN_ROUTE_DONE) result=9;
    else if (outcome.dns_attempted && outcome.dns!=WR_VPN_DNS_DONE) result=11;
    else if (outcome.protocol==WR_VPN_TRANSACTION_UNSAVED) result=10;
    if (result) {
        released=release_failed_up(&resources,&session);
        printf("up\t%u\tcleanup=%s\n",id,release_name(released));
        if (fflush(stdout)) return 3;
    }
    return result;
}
/* Scoped policy first (rule, routes, addresses), then the owned link. */
static int wr_down(int root,unsigned int id)
{
    struct wr_vpn_record record;struct wr_vpn_resources resources;
    struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_config_plan *plan;struct wr_vpn_exec exec={run_ip,NULL};
    enum wr_vpn_store_result stored;enum wr_vpn_runtime_result status;
    enum wr_vpn_lifecycle_result down;int result=0;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    plan=calloc(1,sizeof(*plan));
    if (!plan) return 3;
    if (wr_vpn_prepare_config(&record,plan)==WR_VPN_VALID) {
        if (plan->allowed[0])
            wr_vpn_routes_apply(&plan->resources,plan->allowed,0,&exec);
        if (plan->addresses[0])
            wr_vpn_addresses_apply(plan,0,NULL,0,&exec);
    } else
        /* Unreadable configuration: the rule still has to go. */
        wr_vpn_rule_remove(&resources,&exec);
    memset(plan,0,sizeof(*plan));free(plan);
    status=wr_vpn_runtime_lock(resources.runtime,&runtime);
    if (status!=WR_VPN_RUNTIME_OK) {
        printf("down\t%u\t%s\n",id,status==WR_VPN_RUNTIME_BUSY?"busy":"io");
        return status==WR_VPN_RUNTIME_BUSY?4:3;
    }
    down=wr_vpn_link_release(&runtime,id,&wr_vpn_system_links);
    wr_vpn_runtime_unlock(&runtime);
    printf("down\t%u\t%s\n",id,lifecycle_name(down));
    if (fflush(stdout)) return 3;
    if (down!=WR_VPN_LIFECYCLE_OK) result=6;
    return result;
}
/* Protocol configuration, then addresses, then routes - one sequence. */
static int wr_apply(int root,unsigned int id,const char *protect)
{
    struct wr_vpn_record record;struct wr_vpn_session expected;
    struct wr_vpn_resources resources;struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_apply_options options={NULL,0};struct wr_vpn_apply_outcome outcome;
    struct wr_vpn_exec exec={run_ip,NULL};
    enum wr_vpn_store_result stored;enum wr_vpn_runtime_result status;
    char buffer[256];const char *prefixes[8];int count=0;
    stored=wr_vpn_store_get(root,id,&record);
    if (stored==WR_VPN_STORE_NOT_FOUND) return 5;
    if (stored!=WR_VPN_STORE_OK || !wr_vpn_resources_make(&resources,id,record.protocol)) return 3;
    if (wr_vpn_validate(record.protocol,record.config,record.size)!=WR_VPN_VALID) return 2;
    if (protect && *protect) {
        count=wr_vpn_parse_protect(protect,buffer,sizeof(buffer),prefixes,8);
        if (count<0) return 2;
        options.protected_prefixes=prefixes;options.protected_count=(size_t)count;
    }
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
    if (!wr_vpn_profile_apply(resources.runtime,&record,&expected,&options,&exec,&outcome))
        return 3;
    printf("apply\t%u\tprotocol=%s\taddresses=%s\troutes=%s\n",id,
           transaction_name(outcome.protocol),address_name(outcome.addresses),
           route_name(outcome.routes));
    if (fflush(stdout)) return 3;
    if (outcome.addresses_attempted && outcome.addresses!=WR_VPN_ADDR_DONE) return 8;
    if (outcome.protocol!=WR_VPN_TRANSACTION_DONE &&
        outcome.protocol!=WR_VPN_TRANSACTION_UNSAVED)
        return transaction_status(outcome.protocol);
    if (outcome.routes_attempted && outcome.routes!=WR_VPN_ROUTE_DONE) return 9;
    return outcome.protocol==WR_VPN_TRANSACTION_UNSAVED?10:0;
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
/* Hold across record reads, validation and runtime transitions. Runtime and
 * store locks remain internal and are acquired only after this outer lock.
 * Distinct IDs use distinct locks; read-only commands do not acquire one. */
static int mutation_lock(unsigned int id,int *held)
{
    int directory,fd,busy;char name[32];struct stat st;
    if (mkdir(WR_VPN_RUNTIME_ROOT,0700) && errno!=EEXIST) return 3;
    directory=wr_vpn_store_open(WR_VPN_RUNTIME_ROOT);
    if (directory<0) return 3;
    snprintf(name,sizeof(name),".mutation-%u",id);
    fd=openat(directory,name,O_RDWR|O_CREAT|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK,0600);
    close(directory);
    if(fd<0) return 3;
    if(fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_uid!=geteuid() ||
       st.st_nlink!=1 || (st.st_mode&0777)!=0600) {close(fd);return 3;}
    if(flock(fd,LOCK_EX|LOCK_NB)) {
        busy=errno==EWOULDBLOCK || errno==EAGAIN;close(fd);return busy?4:3;
    }
    *held=fd;return 0;
}
int main(int argc,char **argv)
{
    unsigned int id=0; int root,result,mutation=-1; const char *protect=NULL;
    uint64_t edit_expected=0;
    enum wr_vpn_protocol protocol=WR_VPN_WIREGUARD;
    umask(077);
    if (signal(SIGCHLD,SIG_DFL)==SIG_ERR) return 3;
    if (argc==4 && !strcmp(argv[1],"create")) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
        if (!strcmp(argv[3],"amneziawg")) protocol=WR_VPN_AMNEZIAWG;
        else if (strcmp(argv[3],"wireguard")) return 2;
    } else if (argc==3 && (!strcmp(argv[1],"export") || !strcmp(argv[1],"observe") ||
                           !strcmp(argv[1],"delete") || !strcmp(argv[1],"edit") ||
                           !strcmp(argv[1],"apply") || !strcmp(argv[1],"plan") ||
                           !strcmp(argv[1],"up") || !strcmp(argv[1],"down"))) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
    } else if (argc==4 && !strcmp(argv[1],"edit")) {
        const unsigned char *cursor=(const unsigned char *)argv[3];
        if (!wr_vpn_profile_id(argv[2],&id) || *cursor<'1' || *cursor>'9') return 2;
        for (;*cursor;cursor++) {
            unsigned int digit=(unsigned int)(*cursor-'0');
            if (digit>9 || edit_expected>(UINT64_MAX-digit)/10) return 2;
            edit_expected=edit_expected*10+digit;
        }
        if (edit_expected==UINT64_MAX) return 2;
    } else if (argc==4 && !strcmp(argv[1],"apply")) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
        protect=argv[3];
    } else if (argc==4 && !strcmp(argv[1],"up")) {
        if (!wr_vpn_profile_id(argv[2],&id)) return 2;
        protect=argv[3];
    } else if (!(argc==2 && !strcmp(argv[1],"list"))) return 2;
    if (mkdir(WR_VPN_STORE_ROOT,0700) && errno!=EEXIST) return 3;
    root=wr_vpn_store_open(WR_VPN_STORE_ROOT); if (root<0) return 3;
    if(strcmp(argv[1],"list") && strcmp(argv[1],"export") &&
       strcmp(argv[1],"observe") && strcmp(argv[1],"plan")) {
        result=mutation_lock(id,&mutation);
        if(result) {close(root);return result;}
    }
    if (!strcmp(argv[1],"create")) result=wr_create(root,id,protocol);
    else if (!strcmp(argv[1],"export")) result=wr_export(root,id);
    else if (!strcmp(argv[1],"delete")) result=wr_delete(root,id);
    else if (!strcmp(argv[1],"edit")) result=wr_edit(root,id,edit_expected);
    else if (!strcmp(argv[1],"observe")) result=wr_observe(root,id);
    else if (!strcmp(argv[1],"apply")) result=wr_apply(root,id,protect);
    else if (!strcmp(argv[1],"plan")) result=wr_plan(root,id);
    else if (!strcmp(argv[1],"up")) result=wr_up(root,id,protect);
    else if (!strcmp(argv[1],"down")) result=wr_down(root,id);
    else result=wr_list(root);
    if(mutation>=0) close(mutation);
    close(root); return result;
}
