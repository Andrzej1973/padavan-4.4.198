/* Bounded result/readback formats for reviewed SDK configuration messages.
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
static inline unsigned int wr_iot_config_le32(const unsigned char *p)
{
 return (unsigned int)p[0]|((unsigned int)p[1]<<8)|
        ((unsigned int)p[2]<<16)|((unsigned int)p[3]<<24);
}
/* RF query echoes WiFiStream, Address and Data as three LE words. This
 * decoder matches a previously recorded desired value; it clears no ledger. */
static inline int wr_iot_config_rf_read_matches(
 unsigned int command,unsigned int ext,int is_query,
 unsigned int event,unsigned int event_ext,const unsigned char *payload,
 unsigned int payload_bytes,unsigned int packet_bytes,unsigned int wire_bytes,
 unsigned int header_bytes,unsigned int stream,unsigned int address,unsigned int value)
{
 if(command!=0xedU||ext!=2U||!is_query||event!=0xedU||event_ext!=2U||
    !payload||payload_bytes!=12U||!header_bytes||header_bytes>~0U-12U||
    packet_bytes!=header_bytes+12U||wire_bytes!=packet_bytes)return 0;
 return wr_iot_config_le32(payload)==stream&&
        wr_iot_config_le32(payload+4)==address&&
        wr_iot_config_le32(payload+8)==value;
}
/* Reviewed multi-register query, exactly one MAC record after SDK prefix20. */
static inline int wr_iot_config_mac_read_matches(
 unsigned int command,unsigned int ext,int is_query,unsigned int event,unsigned int event_ext,
 const unsigned char *payload,unsigned int payload_bytes,unsigned int packet_bytes,
 unsigned int wire_bytes,unsigned int header_bytes,unsigned int address,unsigned int value)
{
 if(command!=0xedU||ext!=0x0eU||!is_query||event!=0xedU||event_ext!=0x0eU||
    !payload||payload_bytes!=32U||!header_bytes||header_bytes>~0U-32U||
    packet_bytes!=header_bytes+32U||wire_bytes!=packet_bytes)return 0;
 return wr_iot_config_le32(payload+20)==0U&&
        wr_iot_config_le32(payload+24)==address&&wr_iot_config_le32(payload+28)==value;
}
/* Reviewed channel/TX-power common extended result: command echo byte0,
 * reserved bytes1..3, LE firmware status word4; ext event0 is not command ID. */
static inline int wr_iot_config_ext_command(unsigned int ext)
{return ext==0x08U||ext==0x11U;}
static inline int wr_iot_config_ext_success(unsigned int command,unsigned int ext,
 int is_set,unsigned int event,unsigned int event_ext,const unsigned char *payload,
 unsigned int payload_bytes,unsigned int packet_bytes,unsigned int wire_bytes,
 unsigned int header_bytes)
{
 if(command!=0xedU||!wr_iot_config_ext_command(ext)||!is_set||
    event!=0xedU||event_ext!=0U||!payload||payload_bytes!=8U||!header_bytes||
    header_bytes>~0U-8U||packet_bytes!=header_bytes+8U||wire_bytes!=packet_bytes)return 0;
 return payload[0]==ext&&!(payload[4]|payload[5]|payload[6]|payload[7]);
}
#endif
