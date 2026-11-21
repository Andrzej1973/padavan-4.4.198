/* Candidate only: external callers pin entry to adapter-lifetime lock.
 * Acquires before raw allocator reads chipCap or MCU state. RX allocation
 * remains possible after ordinary TX admission closes. */
static void wr_iot_mcu_message_drop(RTMP_ADAPTER *ad)
{
 ULONG flags=0;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 (void)wr_iot_mcu_message_leave(&ad->wr_iot_mcu_sender_owner);
 wake_up_all(&ad->wr_iot_mcu_sender_wait);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 /* No adapter access after this unlock. */
}
struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad,unsigned int length)
{
 ULONG flags=0;
 int entered;
 struct cmd_msg *msg;
 if(!ad)return NULL;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 entered=wr_iot_mcu_message_enter(&ad->wr_iot_mcu_sender_owner);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 if(!entered)return NULL;
 msg=wr_iot_mcu_alloc_body(ad,length);
 if(!msg)wr_iot_mcu_message_drop(ad);
 /* Success transfers lease to message; destructor drops it after counters. */
 return msg;
}
