/* Candidate helper. Caller pins adapter allocation and is outside RTNL and
 * all driver spinlocks; terminal enqueue closure must already be published.
 * This only joins the command worker, not timer/IRQ/DMA producers. */
INT wr_iot_terminal_command_join_checked(RTMP_ADAPTER *pAd)
{
 ULONG flags = 0;
 unsigned long attempt;
 INT result, recorded;
 if (!pAd || wr_iot_os_join_context()) return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&flags);
 recorded=wr_iot_terminal_command_joined(&pAd->wr_iot_terminal_command,1UL);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->CmdQLock,&flags);
 if (recorded) return NDIS_STATUS_SUCCESS;
 /* Command OS helper rejects creation error pointers, unwraps OS_ABL and
  * compares native task identity. Unknown or self cannot be joined. */
 if (wr_iot_os_command_task_current(&pAd->cmdQTask) != 0)
  return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&flags);
 attempt=wr_iot_terminal_command_join_begin(&pAd->wr_iot_terminal_command,1UL,1);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->CmdQLock,&flags);
 if (!attempt) return NDIS_STATUS_FAILURE;
 result=RtmpOSTaskKill(&pAd->cmdQTask);
 RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&flags);
 recorded=wr_iot_terminal_command_join_finish(&pAd->wr_iot_terminal_command,
   1UL,attempt,result==NDIS_STATUS_SUCCESS);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->CmdQLock,&flags);
 return recorded && result==NDIS_STATUS_SUCCESS ?
   NDIS_STATUS_SUCCESS : NDIS_STATUS_FAILURE;
}
