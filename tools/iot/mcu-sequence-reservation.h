/* Isolated host-side reservation ledger. All calls require one lifetime lock.
 * A lease spans ID selection through message destruction, including the gap
 * before ACK insertion. This proves host exclusion only, not ACK freshness. */
#ifndef WR_IOT_MCU_SEQUENCE_RESERVATION_H
#define WR_IOT_MCU_SEQUENCE_RESERVATION_H
#include "mcu-sequence-slot.h"
struct wr_iot_mcu_sequence_reservation {
 unsigned int occupied,cursor,poisoned,quarantined;
};
static inline unsigned int wr_iot_mcu_sequence_reserve(struct wr_iot_mcu_sequence_reservation *s)
{
 unsigned int slot;
 if(!s||s->poisoned)return 0;
 slot=wr_iot_mcu_sequence_slot(s->cursor,s->occupied|s->quarantined);
 if(slot){s->occupied|=1u<<slot;s->cursor=slot;}
 return slot;
}
static inline int wr_iot_mcu_sequence_release(struct wr_iot_mcu_sequence_reservation *s,unsigned int slot)
{
 if(!s)return 0;
 if(s->poisoned||slot<1||slot>15||!(s->occupied&(1u<<slot))){
  s->poisoned=1;return 0;
 }
 s->occupied&=~(1u<<slot);return 1;
}
/* Timeout leaves the wire transaction unresolved. No reset API is provided:
 * clearing quarantine needs a separately verified transport/firmware epoch. */
static inline int wr_iot_mcu_sequence_finish(
 struct wr_iot_mcu_sequence_reservation *s,unsigned int slot,int uncertain)
{
 if(!wr_iot_mcu_sequence_release(s,slot))return 0;
 if(uncertain)s->quarantined|=1u<<slot;
 return 1;
}
#endif
