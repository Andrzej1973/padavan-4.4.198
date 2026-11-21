#ifndef WR_IOT_COLD_ON_ENTRY_H
#define WR_IOT_COLD_ON_ENTRY_H
#include "radio-entry-result.h"
/* No historical OFF receipt. Read-only selection delegates an absent DOWN
 * proof to the existing native guard; after eligibility, refusal never falls
 * through. Cold admission repeats the proof before claiming any mutation. */
enum wr_iot_radio_entry_result wr_iot_cold_on_entry(int radio_on,int reload);
#endif
