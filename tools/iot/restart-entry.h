#ifndef WR_IOT_RESTART_ENTRY_H
#define WR_IOT_RESTART_ENTRY_H
/* Private RC process context, existing mode0/radio-ON owner only.1 means intent
 * claimed, not restart complete.0 never authorizes stock fallback/reopen;
 * caller must still use existing never-opened admission for any legacy path. */
int wr_iot_restart_entry(int radio_on,int reload);
#endif
