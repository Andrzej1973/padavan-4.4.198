#ifndef WR_IOT_RESTART_MULTICAST_H
#define WR_IOT_RESTART_MULTICAST_H
/* Transport only: caller must separately validate exact current Main/Guest
 * generation and saved policy. bss0=ra0,bss1=ra1; ra2/other names never accepted.
 * SDK !USE_IGMP_SNOOP requires both fast_leave and to_unicast attributes.
 * Apply may partially write; owning controller must mark attempt before call
 * and retain uncertainty instead of automatically replaying this operation. */
int wr_iot_restart_multicast_current(unsigned bss,int enabled);
int wr_iot_restart_multicast_apply(unsigned bss,int enabled);
#endif
