#ifndef WR_IOT_DNS_ACTIVATION_H
#define WR_IOT_DNS_ACTIVATION_H
/* Caller holds the service guard throughout radio activation. Prepare returns
 * errno-style status; commit/abort return 1 on success, 0 retaining recovery.
 * Prepare success retains previous files/leases/UTS/ARP and guard until commit
 * after final radio observation, or abort after BSS and bridge teardown. */
int wr_iot_dns_activation_prepare(void);
int wr_iot_dns_activation_commit(void);
int wr_iot_dns_activation_abort(void);
#endif
