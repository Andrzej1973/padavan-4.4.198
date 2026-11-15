#ifndef WR_IOT_RADIO_ON_AUX_H
#define WR_IOT_RADIO_ON_AUX_H
/* Mode0 keeps WDS/APCLI inactive per pinned SDK. Read-only five fixed names:
 * require absent or administrative DOWN and detached, stable interface index.
 * Not hardware retirement and not permission to close a foreign interface. */
int wr_iot_on_aux_down_current(void);
#endif
