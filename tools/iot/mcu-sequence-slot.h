/* Caller holds ACK queue lock. Occupancy includes every live reservation.
 * Zero means exhausted, never a synchronous command sequence. This helper
 * does not prove freshness against old firmware events or reserve the slot. */
#ifndef WR_IOT_MCU_SEQUENCE_SLOT_H
#define WR_IOT_MCU_SEQUENCE_SLOT_H
static inline unsigned int wr_iot_mcu_sequence_slot(unsigned int previous,
                                                   unsigned int occupied)
{
 unsigned int attempt,slot=previous;
 for(attempt=0;attempt<15;attempt++){
  slot=slot>=15?1:slot+1;
  if(!(occupied&(1u<<slot)))return slot;
 }
 return 0;
}
#endif
