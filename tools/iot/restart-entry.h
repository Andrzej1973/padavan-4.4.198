#ifndef WR_IOT_RESTART_ENTRY_H
#define WR_IOT_RESTART_ENTRY_H
#include "radio-entry-result.h"
/* Private RC process context, existing mode0/radio-ON owner only.1 means intent
 * claimed, not restart complete.0 never authorizes stock fallback/reopen;
 * caller must still use existing never-opened admission for any legacy path. */
int wr_iot_rc_restart_owned(void);
int wr_iot_restart_entry(int radio_on,int reload);
/* Historical RC OFF receipt or separately verified cold DOWN selection.
 * REFUSED must not fall through to SDK; NATIVE retains its existing guard. */
enum wr_iot_radio_entry_result wr_iot_radio_on_entry(int radio_on,int reload);
/* Owned backend OFF only; existing OFF receipt refuses without replacement. */
enum wr_iot_radio_entry_result wr_iot_radio_off_entry(int radio_on,int reload);
#endif
