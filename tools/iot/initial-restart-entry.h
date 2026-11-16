#ifndef WR_IOT_INITIAL_RESTART_ENTRY_H
#define WR_IOT_INITIAL_RESTART_ENTRY_H
#include "radio-entry-result.h"
/* Process-context selector and physical claim. REFUSED must stop the caller;
 * OWNED includes retained cleanup after post-claim refusal. NATIVE delegates
 * only an inapplicable path, never failed driver proof. */
enum wr_iot_radio_entry_result wr_iot_initial_restart_entry(int,int);
#endif
