#ifndef WR_IOT_COLD_ON_SELECT_H
#define WR_IOT_COLD_ON_SELECT_H
#include "precreated-down-wire.h"
enum wr_iot_cold_selection {WR_COLD_SELECT_REFUSED=-1,WR_COLD_SELECT_NATIVE=0,
 WR_COLD_SELECT_ELIGIBLE=1};
/* Read-only selection, not admission. NATIVE preserves the existing SDK
 * never-opened guard; it never grants radio-UP permission. ELIGIBLE must be
 * repeated under the cold root's own fence before any profile/Main mutation.
 * No signal fence, borrowed profile or credentials are retained here. */
enum wr_iot_cold_selection wr_iot_cold_select(const unsigned char *nonce,
 struct wr_iot_down_result *);
#endif
