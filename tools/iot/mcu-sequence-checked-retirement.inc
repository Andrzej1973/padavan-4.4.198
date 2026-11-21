/* Caller holds the same lifetime lock as normal reservation. A checked ID is
 * consumed at first allocation, even if the command subsequently fails before
 * publication. Destruction drops its live lease but never makes the ID reusable.
 * No reset API: retiring this history requires a verified firmware/RX epoch. */
static inline unsigned int wr_iot_mcu_sequence_reserve_checked(
 struct wr_iot_mcu_sequence_reservation *s)
{
 unsigned int slot=wr_iot_mcu_sequence_reserve(s);
 if(slot)s->retired|=1u<<slot;
 return slot;
}
