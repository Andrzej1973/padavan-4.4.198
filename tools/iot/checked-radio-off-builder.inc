/* Adapter-wide OFF, not a per-BSS IoT switch. Candidate only: callers must
 * prove lifecycle exclusion and own the returned message before using it.
 * Does not send, queue, restart or update any software radio flag.
 */
static inline struct cmd_msg *wr_iot_prepare_radio_off(RTMP_ADAPTER *pAd)
{
 struct _EXT_CMD_RADIO_ON_OFF_CTRL_T control;
 struct cmd_msg *msg;
 msg=AndesAllocCmdMsg(pAd,sizeof(control));
 if(!msg)return NULL;
 AndesInitCmdMsg(msg,P1_Q0,EXT_CID,CMD_SET,EXT_CMD_RADIO_ON_OFF_CTRL,
  TRUE,0,FALSE,TRUE,8,NULL,NULL);
 msg->wr_iot_checked=TRUE;
 memset(&control,0,sizeof(control));
 control.ucWiFiRadioCtrl=WIFI_RADIO_OFF;
 AndesAppendCmdMsg(msg,(char *)&control,sizeof(control));
 return msg;
}
