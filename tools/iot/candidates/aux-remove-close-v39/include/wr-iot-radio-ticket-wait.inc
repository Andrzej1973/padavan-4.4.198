/* Candidate-only kernel wait helper. A caller must hold a live adapter pin,
 * snapshot the busy ticket serial under wr_iot_transition_lock, and wait
 * outside that lock. After wake it must recount references and retry claim.
 * Every successful ticket retirement must wake wr_iot_ticket_wait. */
static int wr_iot_ticket_retired_observed(PRTMP_ADAPTER adapter,
 unsigned long serial)
{
 ULONG flags;
 int retired;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 retired=wr_iot_radio_ticket_retired(&adapter->wr_iot_transition,serial);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 return retired;
}

INT wr_iot_wait_ticket_retired(PRTMP_ADAPTER adapter,
 unsigned long serial,unsigned long timeout_jiffies)
{
 if(!adapter||!serial)return -1;
 if(wr_iot_ticket_retired_observed(adapter,serial))return 0;
 if(!timeout_jiffies)return -1;
 return wait_event_timeout(adapter->wr_iot_ticket_wait,
  wr_iot_ticket_retired_observed(adapter,serial),timeout_jiffies)?0:-1;
}
