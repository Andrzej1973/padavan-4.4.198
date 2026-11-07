/* Candidate helper. Caller pins adapter allocation and is outside RTNL and
 * all driver spinlocks; normal/terminal callers share the execution reservation.
 * A successful normal close is retained for subsequent terminal removal.
 * This only joins the command worker, not timer/IRQ/DMA producers. */
INT wr_iot_command_join_shared_checked(RTMP_ADAPTER *pAd)
{
 ULONG flags = 0;
 unsigned long attempt;
 INT result, recorded;
 if (!pAd || wr_iot_os_join_context()) return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&flags);
 recorded=pAd->wr_iot_terminal_command.generation==1UL &&
   pAd->wr_iot_terminal_command.joined &&
   !pAd->wr_iot_terminal_command.joining &&
   !pAd->wr_iot_terminal_command.attaching;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->CmdQLock,&flags);
 if (recorded) return NDIS_STATUS_SUCCESS;
 /* Command OS helper rejects creation error pointers, unwraps OS_ABL and
  * compares native task identity. Unknown or self cannot be joined. */
 if (wr_iot_os_command_task_current(&pAd->cmdQTask) != 0)
  return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&pAd->CmdQLock,&flags);
 attempt=wr_iot_command_normal_join_begin(&pAd->wr_iot_terminal_command,1UL,1);
 if (attempt) pAd->CmdQ.CmdQState=RTMP_TASK_STAT_STOPED;
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
