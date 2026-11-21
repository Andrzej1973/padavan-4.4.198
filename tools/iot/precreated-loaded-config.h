/* Driver-side comparison only. Caller holds the existing configuration owner
 * and adapter/BSS lifetime. Expected PMK must be derived independently from the
 * requested SSID/key using reviewed WPA2 derivation, never copied from loaded
 * state merely to make this check pass. No key is returned or logged.
 * This snapshot alone does not bind userspace requests or exclude later setters. */
#ifndef WR_IOT_PRECREATED_LOADED_CONFIG_H
#define WR_IOT_PRECREATED_LOADED_CONFIG_H
static inline int wr_iot_precreated_loaded_matches(PRTMP_ADAPTER ad,
 PNET_DEV expected_dev,const unsigned char *ssid,unsigned int ssid_length,
 const unsigned char *expected_pmk,unsigned int pmk_length)
{
 unsigned int i,difference=0;
 BSS_STRUCT *bss;
 if(!ad||!expected_dev||!ssid||!expected_pmk||ssid_length<1||ssid_length>32||pmk_length!=32||
    !IS_MT7603(ad)||ad->ApCfg.BssidNum<3||
    ad->ApCfg.BssidNum>sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0]))return 0;
 bss=&ad->ApCfg.MBSSID[2];
 if(bss->wdev.if_dev!=expected_dev||bss->SsidLen!=ssid_length||
    bss->wdev.AuthMode!=Ndis802_11AuthModeWPA2PSK||
    bss->wdev.WepStatus!=Ndis802_11AESEnable||
    bss->wdev.GroupKeyWepStatus!=Ndis802_11AESEnable||bss->wdev.IEEE8021X)return 0;
 for(i=0;i<ssid_length;i++)difference|=bss->Ssid[i]^ssid[i];
 for(i=0;i<32;i++)difference|=bss->PMK[i]^expected_pmk[i];
 return difference==0;
}
#endif
