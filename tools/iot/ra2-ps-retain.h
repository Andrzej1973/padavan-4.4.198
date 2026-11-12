/* Caller already owns the SDK station-maintenance or TxS callback context.
 * Read existing association/queue fields without retaining station pointers. */
#ifndef WR_IOT_RA2_PS_RETAIN_H
#define WR_IOT_RA2_PS_RETAIN_H
static inline int wr_iot_ra2_station(RTMP_ADAPTER *ad,unsigned int wcid)
{
 MAC_TABLE_ENTRY *entry;
 STA_TR_ENTRY *traffic;
 if(!ad||!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    wcid>=MAX_LEN_OF_MAC_TABLE||wcid>=MAX_LEN_OF_TR_TABLE)return 0;
 entry=&ad->MacTab.Content[wcid];
 traffic=&ad->MacTab.tr_entry[wcid];
 return entry->wcid==wcid&&traffic->wcid==wcid&&
        IS_ENTRY_CLIENT(entry)&&entry->Sst==SST_ASSOC&&
        entry->func_tb_idx==2&&traffic->func_tb_idx==2&&
        entry->wdev==&ad->ApCfg.MBSSID[2].wdev&&
        ad->ApCfg.MBSSID[2].wdev.if_dev&&
        traffic->wdev==entry->wdev;
}
static inline int wr_iot_ra2_sleeping_pending(RTMP_ADAPTER *ad,unsigned int wcid)
{
 MAC_TABLE_ENTRY *entry;
 STA_TR_ENTRY *traffic;
 if(!wr_iot_ra2_station(ad,wcid))return 0;
 entry=&ad->MacTab.Content[wcid];
 traffic=&ad->MacTab.tr_entry[wcid];
 return ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq&&
        entry->PsMode==PWR_SAVE&&traffic->PsMode==PWR_SAVE&&
        entry->Aid>0&&entry->Aid<WLAN_MAX_NUM_OF_TIM*8U&&
        entry->NoDataIdleCount<entry->StaIdleTimeout&&traffic->enqCount>0;
}
#endif
