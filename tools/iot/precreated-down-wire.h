/* Proposed Linux-only observation syntax. No firmware command or ioctl route.
 * Serial identifies completed Main close, never IoT CLOSE or future permission. */
#ifndef WR_IOT_PRECREATED_DOWN_WIRE_H
#define WR_IOT_PRECREATED_DOWN_WIRE_H
#include "precreated-idle-wire.h"
#define WR_IOT_DOWN_QUERY 19U
#define WR_IOT_DOWN_REPLY 20U
struct wr_iot_down_result {unsigned long long epoch,generation,main_close_serial;};
static inline int wr_iot_down_query_encode(unsigned char *wire,unsigned int n,const unsigned char *nonce){
 if(!wr_iot_idle_query_encode(wire,n,nonce))return 0;
 wire[4]=WR_IOT_DOWN_QUERY;return 1;
}
static inline int wr_iot_down_query_decode(unsigned char *nonce,const unsigned char *wire,unsigned int n){
 unsigned char copy[64];unsigned int i;
 if(nonce)for(i=0;i<16;i++)nonce[i]=0;
 if(!nonce||!wire||n!=64||wire[4]!=WR_IOT_DOWN_QUERY)return 0;
 for(i=0;i<64;i++)copy[i]=wire[i];
 copy[4]=WR_IOT_IDLE_QUERY;return wr_iot_idle_query_decode(nonce,copy,64);
}
static inline int wr_iot_down_reply_encode(unsigned char *wire,unsigned int n,const unsigned char *nonce,
 unsigned long long epoch,unsigned long long generation,unsigned long long main_close_serial){
 if(!wr_iot_idle_reply_encode(wire,n,nonce,epoch,generation,main_close_serial))return 0;
 wire[4]=WR_IOT_DOWN_REPLY;return 1;
}
static inline int wr_iot_down_reply_decode(struct wr_iot_down_result *out,const unsigned char *nonce,
 const unsigned char *wire,unsigned int n){
 struct wr_iot_idle_result decoded;unsigned char copy[64];unsigned int i;
 if(!out)return 0;
 out->epoch=out->generation=out->main_close_serial=0;
 if(!wire||n!=64||wire[4]!=WR_IOT_DOWN_REPLY)return 0;
 for(i=0;i<64;i++)copy[i]=wire[i];
 copy[4]=WR_IOT_IDLE_REPLY;
 if(!wr_iot_idle_reply_decode(&decoded,nonce,copy,64))return 0;
 out->epoch=decoded.epoch;out->generation=decoded.generation;
 out->main_close_serial=decoded.serial;return 1;
}
#endif
