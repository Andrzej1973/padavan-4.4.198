#ifndef WR_VPN_VALIDATE_PROCESS_H
#define WR_VPN_VALIDATE_PROCESS_H
#include "store.h"
enum wr_vpn_validation { WR_VPN_VALID, WR_VPN_REJECTED, WR_VPN_VALIDATOR_FAILED };
enum wr_vpn_validation wr_vpn_validate(enum wr_vpn_protocol protocol,
                                     const void *data,size_t size);
#endif
