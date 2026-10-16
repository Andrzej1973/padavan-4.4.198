#include "link-lifecycle.h"
const struct wr_vpn_link_ops wr_vpn_system_links={wr_vpn_link_query,wr_vpn_link_create,wr_vpn_link_remove};
static int operations(const struct wr_vpn_link_ops *ops)
{ return ops && ops->query && ops->create && ops->remove; }
static enum wr_vpn_lifecycle_result recover(struct wr_vpn_runtime *runtime,
    struct wr_vpn_session *session,const struct wr_vpn_link_ops *ops)
{
    struct wr_vpn_resources r;struct wr_vpn_link link;struct wr_vpn_session active;
    enum wr_vpn_link_result observed;char owner[64];
    if (!wr_vpn_resources_make(&r,session->id,session->protocol) ||
        !wr_vpn_session_owner(session,owner,sizeof(owner))) return WR_VPN_LIFECYCLE_REFUSED;
    observed=ops->query(r.interface,&link);
    if (observed==WR_VPN_LINK_ABSENT) return WR_VPN_LIFECYCLE_UNKNOWN;
    if (observed!=WR_VPN_LINK_PRESENT) return WR_VPN_LIFECYCLE_UNKNOWN;
    if (!wr_vpn_link_owned(&r,&link,session->index?session->index:link.index,owner)) return WR_VPN_LIFECYCLE_REFUSED;
    if (!session->index) {
        active=*session;active.index=link.index;
        if (wr_vpn_runtime_put(runtime,&active,session)!=WR_VPN_RUNTIME_OK) return WR_VPN_LIFECYCLE_UNKNOWN;
        *session=active;
    }
    return WR_VPN_LIFECYCLE_OK;
}
enum wr_vpn_lifecycle_result wr_vpn_link_acquire(struct wr_vpn_runtime *runtime,unsigned int id,
    enum wr_vpn_protocol protocol,uint64_t revision,const struct wr_vpn_link_ops *ops,struct wr_vpn_session *out)
{
    struct wr_vpn_session s;struct wr_vpn_resources r;struct wr_vpn_link link;
    enum wr_vpn_runtime_result stored;enum wr_vpn_link_result observed;
    enum wr_vpn_lifecycle_result result;
    if (!out || !operations(ops) || !revision || !wr_vpn_resources_make(&r,id,protocol)) return WR_VPN_LIFECYCLE_REFUSED;
    stored=wr_vpn_runtime_read(runtime,id,&s);
    if (stored==WR_VPN_RUNTIME_OK) {
        if (s.protocol!=protocol || s.revision!=revision) return WR_VPN_LIFECYCLE_REFUSED;
        result=recover(runtime,&s,ops);
        if (result==WR_VPN_LIFECYCLE_OK) *out=s;
        /* Missing recorded link requires explicit release; never silently recreate. */
        return result;
    }
    if (stored!=WR_VPN_RUNTIME_ABSENT) return WR_VPN_LIFECYCLE_REFUSED;
    observed=ops->query(r.interface,&link);
    if (observed==WR_VPN_LINK_UNKNOWN) return WR_VPN_LIFECYCLE_UNKNOWN;
    if (observed!=WR_VPN_LINK_ABSENT) return WR_VPN_LIFECYCLE_REFUSED;
    if (!wr_vpn_session_new(&s,id,protocol,revision) ||
        wr_vpn_runtime_put(runtime,&s,NULL)!=WR_VPN_RUNTIME_OK) return WR_VPN_LIFECYCLE_UNKNOWN;
    /* Intent is visible before any kernel mutation. Ignore return hints: only
     * an independent session-tagged query can establish the actual outcome. */
    (void)ops->create(&s,&link);
    result=recover(runtime,&s,ops);
    if (result==WR_VPN_LIFECYCLE_OK) { *out=s;return result; }
    /* On unknown state retain the intent. Proven absence permits its removal. */
    if (ops->query(r.interface,&link)==WR_VPN_LINK_ABSENT)
        (void)wr_vpn_runtime_clear(runtime,&s);
    return result;
}
enum wr_vpn_lifecycle_result wr_vpn_link_release(struct wr_vpn_runtime *runtime,unsigned int id,const struct wr_vpn_link_ops *ops)
{
    struct wr_vpn_session s;struct wr_vpn_resources r;struct wr_vpn_link link;
    enum wr_vpn_runtime_result stored;enum wr_vpn_lifecycle_result recovered;
    if (!operations(ops) || !id || id>WR_VPN_PROFILE_ID_MAX) return WR_VPN_LIFECYCLE_REFUSED;
    stored=wr_vpn_runtime_read(runtime,id,&s);
    if (stored==WR_VPN_RUNTIME_ABSENT) {
        /* No session cannot authorize removal of any observed link. */
        if (!wr_vpn_resources_make(&r,id,WR_VPN_WIREGUARD)) return WR_VPN_LIFECYCLE_REFUSED;
        return ops->query(r.interface,&link)==WR_VPN_LINK_ABSENT?WR_VPN_LIFECYCLE_OK:WR_VPN_LIFECYCLE_REFUSED;
    }
    if (stored!=WR_VPN_RUNTIME_OK || !wr_vpn_resources_make(&r,id,s.protocol)) return WR_VPN_LIFECYCLE_REFUSED;
    if (ops->query(r.interface,&link)==WR_VPN_LINK_ABSENT)
        return wr_vpn_runtime_clear(runtime,&s)==WR_VPN_RUNTIME_OK?WR_VPN_LIFECYCLE_OK:WR_VPN_LIFECYCLE_UNKNOWN;
    recovered=recover(runtime,&s,ops);if (recovered!=WR_VPN_LIFECYCLE_OK) return recovered;
    (void)ops->remove(&s);
    if (ops->query(r.interface,&link)!=WR_VPN_LINK_ABSENT) return WR_VPN_LIFECYCLE_UNKNOWN;
    return wr_vpn_runtime_clear(runtime,&s)==WR_VPN_RUNTIME_OK?WR_VPN_LIFECYCLE_OK:WR_VPN_LIFECYCLE_UNKNOWN;
}
