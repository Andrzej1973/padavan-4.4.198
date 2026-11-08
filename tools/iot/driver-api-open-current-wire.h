/* Current OPEN reference observation. No RF/client acceptance, configuration
 * lease or permission survives this response; CLOSE must revalidate under its
 * own ticket/owner. Proposed wire extension, no endpoint installed here. */
#ifndef WR_IOT_DRIVER_API_OPEN_CURRENT_WIRE_H
#define WR_IOT_DRIVER_API_OPEN_CURRENT_WIRE_H
#include "driver-api-close-wire.h"
struct wr_iot_driver_open_current_result {
 unsigned long long adapter_epoch,device_generation,open_token;
};
static inline int wr_iot_driver_open_current_query_encode(unsigned char *wire,
 unsigned int length,const unsigned char *nonce){
 if(!wr_iot_driver_closed_query_encode(wire,length,nonce))return 0;
 wire[4]=11;return 1;
}
static inline int wr_iot_driver_open_current_query_decode(unsigned char *nonce,
 const unsigned char *wire,unsigned int length){
 unsigned char copy[64];unsigned int i;
 if(nonce)for(i=0;i<16;i++)nonce[i]=0;
 if(!nonce||!wire||length!=64||wire[4]!=11)return 0;
 for(i=0;i<64;i++)copy[i]=wire[i];
 copy[4]=4;
 return wr_iot_driver_closed_query_decode(nonce,copy,64);
}
static inline int wr_iot_driver_open_current_encode(unsigned char *wire,unsigned int length,
 const unsigned char *nonce,unsigned long long epoch,unsigned long long generation,
 unsigned long long token){
 struct wr_iot_driver_close_request request;unsigned int i;
 if(!wire||length!=64)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!nonce)return 0;
 for(i=0;i<16;i++)request.open_request_id[i]=nonce[i];
 request.adapter_epoch=epoch;request.device_generation=generation;request.open_token=token;
 if(!wr_iot_driver_close_request_encode(wire,length,&request))return 0;
 wire[4]=12;return 1;
}
static inline int wr_iot_driver_open_current_decode(struct wr_iot_driver_open_current_result *out,
 const unsigned char *nonce,unsigned long long epoch,unsigned long long generation,
 const unsigned char *wire,unsigned int length){
 unsigned char copy[64];unsigned int i,difference=0,nonzero=0;
 struct wr_iot_driver_close_request observed;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=out->open_token=0;
 if(!nonce||!epoch||!generation||!wire||length!=64||wire[4]!=12)return 0;
 for(i=0;i<64;i++)copy[i]=wire[i];
 copy[4]=10;
 if(!wr_iot_driver_close_request_decode(&observed,copy,64)||
    observed.adapter_epoch!=epoch||observed.device_generation!=generation)return 0;
 for(i=0;i<16;i++){difference|=nonce[i]^observed.open_request_id[i];nonzero|=nonce[i];}
 if(difference||!nonzero)return 0;
 out->adapter_epoch=epoch;out->device_generation=generation;out->open_token=observed.open_token;return 1;
}
#endif
