#if defined(BOARD_WR1200JS)
#include "wr-devices/radio-query.h"
#include "wr-devices/radio-merge.h"
#include "wr-devices/rssi-collector.h"
#if defined(__mips__)
_Static_assert(sizeof(RT_802_11_MAC_TABLE)==1796,"WR station table must match the 64-client driver ABI");
#endif
static int wr_device_radio_ioctl(const char *interface, int command,
                                 struct iwreq *request, void *context)
{
    (void)context;
    return wl_ioctl(interface, command, request);
}
void wr_device_collect_rssi(struct wr_rssi_collector *collector,unsigned long long now)
{
 const char *interfaces[2]={IFNAME_2G_MAIN,IFNAME_5G_MAIN};
 wr_rssi_collector_tick(collector,interfaces,wr_device_radio_ioctl,NULL,now);
}
int wr_device_collect_radio(struct wr_device_snapshot *networkmap)
{
    struct wr_radio_snapshot two, five;
    struct wr_device_joined_snapshot joined;
    int two_disabled = nvram_match("rt_radio_x", "0");
    int five_disabled = nvram_match("wl_radio_x", "0");
    if (!networkmap) return 0;
#if defined(USE_IWPRIV_RADIO_2G)
    two_disabled |= nvram_match("mlme_radio_rt", "0");
#endif
#if defined(USE_IWPRIV_RADIO_5G)
    five_disabled |= nvram_match("mlme_radio_wl", "0");
#endif
    memset(&two, 0, sizeof(two));
    memset(&five, 0, sizeof(five));
    if (!two_disabled && !wr_radio_query(IFNAME_2G_MAIN,
        nvram_wlan_get_int(0, "stream_rx"), wr_device_radio_ioctl, NULL, &two)) return 0;
    if (!five_disabled && !wr_radio_query(IFNAME_5G_MAIN,
        nvram_wlan_get_int(1, "stream_rx"), wr_device_radio_ioctl, NULL, &five)) return 0;
    if (!wr_device_radio_merge(networkmap, &two, &five, &joined)) return 0;
    *networkmap = joined.networkmap;
    return 1;
}
#endif
