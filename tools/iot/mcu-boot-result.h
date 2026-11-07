/* Pinned MT7603 init-command protocol only. Response status is the ext_eid
 * byte of the final RX header word, not an extended RadioOnOff payload.
 * Sequence binding, transport lifetime and firmware epoch are separate. */
#ifndef WR_IOT_MCU_BOOT_RESULT_H
#define WR_IOT_MCU_BOOT_RESULT_H
static inline int wr_iot_mcu_boot_command(unsigned int command,unsigned int ext)
{
 return ext==0U&&(command==0x01U||command==0x02U||command==0xefU);
}
static inline int wr_iot_mcu_boot_success(unsigned int command,unsigned int ext,
 unsigned int event,unsigned int status,unsigned int packet_bytes,
 unsigned int wire_bytes,unsigned int header_bytes)
{
 unsigned int expected=command==0xefU?0xefU:0x01U;
 return wr_iot_mcu_boot_command(command,ext)&&header_bytes&&
        packet_bytes==header_bytes&&wire_bytes==header_bytes&&
        event==expected&&status==0U;
}
#endif
