/* Caller pins adapter and owns the CLOSE serial. Must run outside sender
 * invocations and all locks, with RX/IRQ still available for an owned OFF.
 * This is sender invocation drain, never DMA or queue-consumer completion. */
static int wr_iot_mcu_senders_drained(RTMP_ADAPTER *ad)
{
 ULONG flags=0;
 int ready;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 ready=wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 return ready;
}
INT wr_iot_mcu_sender_close_drain(RTMP_ADAPTER *ad,unsigned long serial)
{
 ULONG flags=0;
 int accepted;
 if(!ad||!serial||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 accepted=wr_iot_mcu_sender_close(&ad->wr_iot_mcu_sender_owner,serial);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 if(!accepted)return NDIS_STATUS_FAILURE;
 if(!wait_event_timeout(ad->wr_iot_mcu_sender_wait,
      wr_iot_mcu_senders_drained(ad),msecs_to_jiffies(5000)))
  return NDIS_STATUS_FAILURE;
 return NDIS_STATUS_SUCCESS;
}
