/* MT7603 extended RadioOnOff result payload, from pinned andes_mt.h.
 * This checks payload syntax/status only. The transport must separately bind
 * it to the current OFF request and prove callback lifetime/completion.
 * The payload has no ON/OFF echo; do not infer OFF from this parser alone. */
#ifndef WR_IOT_RADIO_RESULT_H
#define WR_IOT_RADIO_RESULT_H
#ifdef __KERNEL__
#include <linux/types.h>
#else
#include <stddef.h>
#endif
#define WR_IOT_RADIO_EXT_COMMAND 0x05u
#define WR_IOT_RADIO_RESULT_SIZE 8u
static inline int wr_iot_radio_result_success(const void *payload,size_t size){
 const unsigned char *bytes=payload;unsigned long status;
 if(!bytes||size!=WR_IOT_RADIO_RESULT_SIZE||bytes[0]!=WR_IOT_RADIO_EXT_COMMAND)return 0;
 /* Reserved bytes 1..3 are unspecified. Byte loads permit unaligned payloads
  * and avoid mutating a receive buffer while converting little endian. */
 status=(unsigned long)bytes[4]|((unsigned long)bytes[5]<<8)|
        ((unsigned long)bytes[6]<<16)|((unsigned long)bytes[7]<<24);
 return status==0;
}
#endif
