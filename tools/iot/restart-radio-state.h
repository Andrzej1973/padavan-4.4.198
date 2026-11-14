#ifndef WR_IOT_RESTART_RADIO_STATE_H
#define WR_IOT_RESTART_RADIO_STATE_H
/* Fixed WR mode0/radio-ON SDK state update before Main UP. Caller records one
 * attempt before calling. Partial writes are uncertainty, not permission to
 * retry or start Main. reload0 never writes reload_svc_rt. Its event can be
 * consumed by watchdog immediately; success does not prove delivery. No flash commit. */
int wr_iot_rc_restart_radio_state(int reload);
#endif
