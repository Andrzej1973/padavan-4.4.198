/* Prepared FT frame length admission; caller supplies trusted buffer capacity.
 * This validates outer lengths only, not IE contents or association ownership. */
#ifndef WR_IOT_FT_ACTION_BOUNDS_H
#define WR_IOT_FT_ACTION_BOUNDS_H
static inline int wr_iot_ft_action_payload_length(unsigned long frame_length,
 unsigned long capacity,unsigned long mac_header,unsigned long action_header,
 unsigned short *payload)
{
 unsigned long rest;
 if(!payload||frame_length>capacity||frame_length<mac_header)return 0;
 rest=frame_length-mac_header;
 if(rest<action_header||rest>65535UL)return 0;
 *payload=(unsigned short)(rest-action_header);
 return 1;
}
#endif
