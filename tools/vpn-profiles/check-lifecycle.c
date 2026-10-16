#define _GNU_SOURCE
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include "link-lifecycle.h"
static struct wr_vpn_runtime runtime={-1,-1};
static struct wr_vpn_link links[3];
static unsigned int creates,removes;
static int query_unknown,create_missing,remove_failed;
static unsigned int id_from_name(const char *name)
{
    unsigned int id;assert(!strncmp(name,"wrvpn",5) && wr_vpn_profile_id(name+5,&id) && id<3);return id;
}
static enum wr_vpn_link_result query(const char *name,struct wr_vpn_link *out)
{
    unsigned int id=id_from_name(name);memset(out,0,sizeof(*out));
    if (query_unknown) return WR_VPN_LINK_UNKNOWN;
    if (!links[id].index) return WR_VPN_LINK_ABSENT;
    *out=links[id];return WR_VPN_LINK_PRESENT;
}
static enum wr_vpn_action_result create(const struct wr_vpn_session *s,struct wr_vpn_link *out)
{
    struct wr_vpn_session intent;struct wr_vpn_resources r;struct wr_vpn_link *link=&links[s->id];
    assert(wr_vpn_runtime_read(&runtime,s->id,&intent)==WR_VPN_RUNTIME_OK && !intent.index);
    assert(!memcmp(intent.nonce,s->nonce,16) && !link->index);
    creates++;if (create_missing) return WR_VPN_ACTION_UNKNOWN;
    assert(wr_vpn_resources_make(&r,s->id,s->protocol));
    link->index=40+s->id;strcpy(link->name,r.interface);
    strcpy(link->kind,s->protocol==WR_VPN_WIREGUARD?"wireguard":"amneziawg");
    assert(wr_vpn_session_owner(s,link->owner,sizeof(link->owner)));*out=*link;
    /* Deliberately lose ACK despite applied kernel change. */
    return WR_VPN_ACTION_UNKNOWN;
}
static enum wr_vpn_action_result remove_link(const struct wr_vpn_session *s)
{
    struct wr_vpn_resources r;char owner[64];
    assert(wr_vpn_resources_make(&r,s->id,s->protocol));assert(wr_vpn_session_owner(s,owner,sizeof(owner)));
    assert(wr_vpn_link_owned(&r,&links[s->id],s->index,owner));removes++;
    if (!remove_failed) memset(&links[s->id],0,sizeof(links[s->id]));
    return WR_VPN_ACTION_UNKNOWN;
}
int main(void)
{
    char path[]="/tmp/wrvpn-lifecycle-XXXXXX",name[256];
    const struct wr_vpn_link_ops ops={query,create,remove_link};
    struct wr_vpn_session awg,wg,intent,out;unsigned int prior;
    assert(mkdtemp(path));assert(wr_vpn_runtime_lock(path,&runtime)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_link_acquire(&runtime,1,WR_VPN_AMNEZIAWG,1,&ops,&awg)==WR_VPN_LIFECYCLE_OK && awg.index==41);
    assert(wr_vpn_link_acquire(&runtime,2,WR_VPN_WIREGUARD,1,&ops,&wg)==WR_VPN_LIFECYCLE_OK && wg.index==42);
    prior=creates;assert(wr_vpn_link_acquire(&runtime,1,WR_VPN_AMNEZIAWG,1,&ops,&out)==WR_VPN_LIFECYCLE_OK && creates==prior);
    assert(wr_vpn_link_acquire(&runtime,1,WR_VPN_WIREGUARD,1,&ops,&out)==WR_VPN_LIFECYCLE_REFUSED);
    assert(wr_vpn_link_acquire(&runtime,1,WR_VPN_AMNEZIAWG,2,&ops,&out)==WR_VPN_LIFECYCLE_REFUSED);
    remove_failed=1;assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_UNKNOWN);
    assert(wr_vpn_runtime_read(&runtime,2,&out)==WR_VPN_RUNTIME_OK && out.index==wg.index);
    remove_failed=0;assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_OK);
    assert(links[1].index==awg.index && wr_vpn_runtime_read(&runtime,1,&out)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_OK);
    create_missing=1;assert(wr_vpn_link_acquire(&runtime,2,WR_VPN_WIREGUARD,2,&ops,&out)==WR_VPN_LIFECYCLE_UNKNOWN);
    assert(wr_vpn_runtime_read(&runtime,2,&out)==WR_VPN_RUNTIME_ABSENT);create_missing=0;
    /* Crash after kernel create but before publishing index: recover only nonce. */
    assert(wr_vpn_session_new(&intent,2,WR_VPN_WIREGUARD,2));
    assert(wr_vpn_runtime_put(&runtime,&intent,NULL)==WR_VPN_RUNTIME_OK);
    assert(create(&intent,&links[2])==WR_VPN_ACTION_UNKNOWN);
    prior=creates;assert(wr_vpn_link_acquire(&runtime,2,WR_VPN_WIREGUARD,2,&ops,&wg)==WR_VPN_LIFECYCLE_OK && wg.index==42 && creates==prior);
    strcpy(links[2].owner,"foreign");prior=removes;
    assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_REFUSED && removes==prior);
    assert(wr_vpn_session_owner(&wg,links[2].owner,sizeof(links[2].owner)));
    query_unknown=1;assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_UNKNOWN && removes==prior);query_unknown=0;
    assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_OK);
    assert(wr_vpn_link_release(&runtime,1,&ops)==WR_VPN_LIFECYCLE_OK);
    assert(wr_vpn_session_new(&intent,2,WR_VPN_WIREGUARD,3));assert(wr_vpn_runtime_put(&runtime,&intent,NULL)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_link_acquire(&runtime,2,WR_VPN_WIREGUARD,3,&ops,&out)==WR_VPN_LIFECYCLE_UNKNOWN);
    assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_OK);
    links[2].index=99;prior=creates;
    assert(wr_vpn_link_acquire(&runtime,2,WR_VPN_WIREGUARD,3,&ops,&out)==WR_VPN_LIFECYCLE_REFUSED && creates==prior);
    assert(wr_vpn_link_release(&runtime,2,&ops)==WR_VPN_LIFECYCLE_REFUSED);
    wr_vpn_runtime_unlock(&runtime);snprintf(name,sizeof(name),"%s/.operation-lock",path);assert(!unlink(name));assert(!rmdir(path));
    puts("PASS VPN link lifecycle: real private session files, independent profiles, intent-before-create, lost ACK/index recovery, foreign refusal, retained state after uncertain cleanup; mock network, no configured VPN proof");
    return 0;
}
