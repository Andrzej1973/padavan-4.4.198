/* Pinned SDK multiple-MAC-register write response only.
 * Sequence/ticket ownership and transport completion are separate gates. */
#ifndef WR_IOT_MCU_CONFIG_RESULT_H
#define WR_IOT_MCU_CONFIG_RESULT_H
#define WR_IOT_CONFIG_MULTI_WRITE_SIZE 32U
static inline int wr_iot_config_multi_write_success(
 unsigned int command,unsigned int ext,int is_set,
 unsigned int event,unsigned int event_ext,
 const unsigned char *payload,unsigned int payload_bytes,
 unsigned int packet_bytes,unsigned int wire_bytes,unsigned int header_bytes)
{
 if(command!=0xedU||ext!=0x0eU||!is_set||event!=0xedU||event_ext!=0x0eU||
    !payload||payload_bytes!=WR_IOT_CONFIG_MULTI_WRITE_SIZE||!header_bytes||
    header_bytes>~0U-WR_IOT_CONFIG_MULTI_WRITE_SIZE||
    packet_bytes!=header_bytes+WR_IOT_CONFIG_MULTI_WRITE_SIZE||
    wire_bytes!=packet_bytes)return 0;
 /* SDK CmdMultipleMacRegAccessWriteCb reads LE u4Status at payload offset20.
  * Byte-wise comparison avoids alignment and host-endian assumptions. */
 return !(payload[20]|payload[21]|payload[22]|payload[23]);
}
#endif
