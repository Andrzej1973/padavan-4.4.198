/* Linux configuration observation only: initial never-opened ra2.
 * Not an OPEN/loaded-key/RF receipt. No endpoint installed by this codec. */
#ifndef WR_IOT_PRECREATED_IDLE_WIRE_H
#define WR_IOT_PRECREATED_IDLE_WIRE_H
#include "driver-api-wire.h"
#define WR_IOT_IDLE_QUERY 17U
#define WR_IOT_IDLE_REPLY 18U
struct wr_iot_idle_result {unsigned long long epoch,generation,serial;};
static inline int wr_iot_idle_query_encode(unsigned char *wire,unsigned int n,const unsigned char *nonce){
 if(!wr_iot_driver_closed_query_encode(wire,n,nonce))return 0;
 wire[4]=WR_IOT_IDLE_QUERY;return 1;
}
static inline int wr_iot_idle_query_decode(unsigned char *nonce,const unsigned char *wire,unsigned int n){
 unsigned char copy[64];unsigned int i;
 if(nonce)for(i=0;i<16;i++)nonce[i]=0;
 if(!nonce||!wire||n!=64||wire[4]!=WR_IOT_IDLE_QUERY)return 0;
 for(i=0;i<64;i++)copy[i]=wire[i];
 copy[4]=4;return wr_iot_driver_closed_query_decode(nonce,copy,64);
}
static inline int wr_iot_idle_reply_encode(unsigned char *wire,unsigned int n,const unsigned char *nonce,
 unsigned long long epoch,unsigned long long generation,unsigned long long serial){
 if(!wire||n!=64)return 0;
 {unsigned int i;for(i=0;i<64;i++)wire[i]=0;}
 if(!epoch||!generation||!serial||!wr_iot_idle_query_encode(wire,n,nonce))return 0;
 wire[4]=WR_IOT_IDLE_REPLY;wr_iot_driver_put64(wire+24,epoch);
 wr_iot_driver_put64(wire+32,generation);wr_iot_driver_put64(wire+40,serial);return 1;
}
static inline int wr_iot_idle_reply_decode(struct wr_iot_idle_result *out,const unsigned char *nonce,
 const unsigned char *wire,unsigned int n){
 unsigned int i,difference=0,nonzero=0;
 if(!out)return 0;
 out->epoch=out->generation=out->serial=0;
 if(!nonce||!wire||n!=64||wire[0]!='W'||wire[1]!='R'||wire[2]!='I'||wire[3]!='2'||wire[4]!=WR_IOT_IDLE_REPLY)return 0;
 for(i=5;i<8;i++)if(wire[i])return 0;
 for(i=48;i<64;i++)if(wire[i])return 0;
 for(i=0;i<16;i++){difference|=nonce[i]^wire[8+i];nonzero|=nonce[i];}
 if(difference||!nonzero||!wr_iot_driver_get64(wire+24)||!wr_iot_driver_get64(wire+32)||!wr_iot_driver_get64(wire+40))return 0;
 out->epoch=wr_iot_driver_get64(wire+24);out->generation=wr_iot_driver_get64(wire+32);
 out->serial=wr_iot_driver_get64(wire+40);return 1;
}
#endif
