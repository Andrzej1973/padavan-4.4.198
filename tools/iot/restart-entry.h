#ifndef WR_IOT_RESTART_ENTRY_H
#define WR_IOT_RESTART_ENTRY_H
/* Private RC process context, existing mode0/radio-ON owner only.1 means intent
 * claimed, not restart complete.0 never authorizes stock fallback/reopen;
 * caller must still use existing never-opened admission for any legacy path. */
int wr_iot_rc_restart_owned(void);
int wr_iot_restart_entry(int radio_on,int reload);
enum wr_iot_radio_entry_result {WR_RADIO_ENTRY_NATIVE=0,WR_RADIO_ENTRY_OWNED=1,WR_RADIO_ENTRY_REFUSED=2};
/* Historical RC OFF receipt only. REFUSED must not fall through to SDK. */
enum wr_iot_radio_entry_result wr_iot_radio_on_entry(int radio_on,int reload);
/* Owned backend OFF only; existing OFF receipt refuses without replacement. */
enum wr_iot_radio_entry_result wr_iot_radio_off_entry(int radio_on,int reload);
#endif
