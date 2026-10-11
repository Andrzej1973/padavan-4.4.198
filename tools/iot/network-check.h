#ifndef WR_IOT_NETWORK_CHECK_H
#define WR_IOT_NETWORK_CHECK_H
int wr_iot_network_check(const char *,const char *,const char *,const char *);
/* Caller holds service guard. Protocol checks do not open BSS or change files. */
int wr_iot_network_services_ready(const char *);
#endif
