#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "config-transaction.h"
#include <string.h>

static int same_session(const struct wr_vpn_session *a,const struct wr_vpn_session *b)
{
    return a->id==b->id && a->protocol==b->protocol && a->revision==b->revision &&
        a->index==b->index && !memcmp(a->nonce,b->nonce,sizeof(a->nonce));
}

/* Only a record for the same profile and protocol can restore this interface. */
static int usable_rollback(const struct wr_vpn_record *rollback,
                           const struct wr_vpn_record *record)
{
    return rollback && rollback->id==record->id && rollback->protocol==record->protocol &&
        rollback->size && rollback->size<=WR_VPN_CONFIG_MAX;
}

enum wr_vpn_transaction_result wr_vpn_config_transaction(
    const char *runtime_root,const struct wr_vpn_record *record,
    const struct wr_vpn_session *expected,const struct wr_vpn_record *rollback)
{
    struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_session current,after;
    enum wr_vpn_runtime_result status;
    enum wr_vpn_apply_result applied;
    enum wr_vpn_readback_result checked;
    enum wr_vpn_transaction_result result;

    if (!runtime_root || !record || !expected) return WR_VPN_TRANSACTION_REFUSED;

    status=wr_vpn_runtime_lock(runtime_root,&runtime);
    if (status==WR_VPN_RUNTIME_BUSY) return WR_VPN_TRANSACTION_BUSY;
    if (status==WR_VPN_RUNTIME_ABSENT) return WR_VPN_TRANSACTION_ABSENT;
    if (status!=WR_VPN_RUNTIME_OK) return WR_VPN_TRANSACTION_IO;

    status=wr_vpn_runtime_read(&runtime,record->id,&current);
    if (status==WR_VPN_RUNTIME_ABSENT) { result=WR_VPN_TRANSACTION_ABSENT;goto done; }
    if (status!=WR_VPN_RUNTIME_OK) { result=WR_VPN_TRANSACTION_IO;goto done; }

    /* The session must still be the one the caller decided to act on, and it
     * must describe this profile revision with an interface already created. */
    if (!same_session(&current,expected) || current.protocol!=record->protocol ||
        current.revision!=record->revision || !current.index) {
        result=WR_VPN_TRANSACTION_STALE;goto done;
    }

    applied=wr_vpn_config_apply(record);
    if (applied==WR_VPN_APPLY_REFUSED || applied==WR_VPN_APPLY_NOT_STARTED) {
        result=WR_VPN_TRANSACTION_REFUSED;goto done;
    }
    if (applied!=WR_VPN_APPLY_ACKNOWLEDGED) { result=WR_VPN_TRANSACTION_UNKNOWN;goto done; }

    checked=wr_vpn_config_readback(record,current.index);
    if (checked==WR_VPN_READBACK_UNKNOWN) { result=WR_VPN_TRANSACTION_UNKNOWN;goto done; }
    if (checked==WR_VPN_READBACK_MATCH) {
        /* Ownership is bookkeeping here: another session may have replaced
         * ours while the transport ran. */
        status=wr_vpn_runtime_read(&runtime,record->id,&after);
        result=(status==WR_VPN_RUNTIME_OK && same_session(&after,&current))?
            WR_VPN_TRANSACTION_DONE:WR_VPN_TRANSACTION_UNKNOWN;
        goto done;
    }

    /* The kernel does not hold what we asked for. Restore the previous record
     * when the caller supplied one, and require the rollback to read back. */
    if (!usable_rollback(rollback,record)) { result=WR_VPN_TRANSACTION_MISMATCH;goto done; }
    applied=wr_vpn_config_apply(rollback);
    checked=applied==WR_VPN_APPLY_ACKNOWLEDGED?
        wr_vpn_config_readback(rollback,current.index):WR_VPN_READBACK_UNKNOWN;
    result=checked==WR_VPN_READBACK_MATCH?WR_VPN_TRANSACTION_MISMATCH:
        WR_VPN_TRANSACTION_ROLLBACK_FAILED;

done:
    wr_vpn_runtime_unlock(&runtime);
    return result;
}
