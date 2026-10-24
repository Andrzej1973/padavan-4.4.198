#ifndef WR_IOT_DNS_ACTIVATION_H
#define WR_IOT_DNS_ACTIVATION_H
/* Caller holds the service guard throughout radio activation. Prepare returns
 * errno-style status; commit/abort return 1 on success, 0 retaining recovery.
 * Prepare success retains previous files/leases/UTS/ARP and guard until commit
 * after final radio observation, or abort after BSS and bridge teardown. */
/* Commit releases this startup transaction's baseline. Abort is available
 * only before commit; it is not the normal OFF operation after ACTIVE.
 * Normal disable must use a fresh guarded service transaction based on the
 * current configuration and remove only owned IoT resources. Do not leave
 * this startup guard held throughout ACTIVE just to retain rollback files. */
int wr_iot_dns_activation_prepare(void);
int wr_iot_dns_activation_commit(void);
int wr_iot_dns_activation_abort(void);
/* Normal OFF: caller has quiesced BSS and closed all three gates under its
 * guard. An existing bridge must be owned; keep it until service commit so
 * service failure can recover the current baseline. Captures a NEW baseline, regenerates normal
 * services, and retains service recovery until disable_commit succeeds.
 * On failure keep outer quarantine; activation_abort may recover this new
 * service baseline but must never reopen the removed IoT radio/bridge. */
/* Repeating disable_prepare on its own prepared transaction only re-observes
 * readiness; it never restarts the daemon or replaces the saved baseline. */
int wr_iot_dns_disable_prepare(void);
int wr_iot_dns_disable_commit(void);
#endif
