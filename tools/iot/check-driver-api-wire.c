#include <assert.h>
#include <string.h>
#include "driver-api-wire.h"
int main(void){unsigned char w[144]={ 'W','R','I','2',1};struct wr_iot_driver_open_request r;
w[15]=1;w[23]=2;w[24]=3;w[40]=3;w[41]=8;memcpy(w+48,"IoT",3);memcpy(w+80,"password",8);
assert(wr_iot_driver_open_decode(&r,w,144));assert(r.adapter_epoch==1&&r.device_generation==2&&!strcmp((char*)r.ssid,"IoT"));
for(unsigned n=0;n<160;n++)if(n!=144){assert(!wr_iot_driver_open_decode(&r,w,n));for(unsigned i=0;i<sizeof r;i++)assert(!((unsigned char*)&r)[i]);}
for(unsigned i=0;i<144;i++)if((i>=5&&i<8)||(i>=42&&i<48)||(i>=51&&i<80)||i>=88){w[i]=1;assert(!wr_iot_driver_open_decode(&r,w,144));w[i]=0;}
for(unsigned i=0;i<256;i++){w[40]=i;assert(wr_iot_driver_open_decode(&r,w,144)==(i==3));}w[40]=3;
for(unsigned i=0;i<256;i++){w[41]=i;assert(wr_iot_driver_open_decode(&r,w,144)==(i==8));}w[41]=8;
unsigned char response[32];struct wr_iot_driver_identity identity;
assert(wr_iot_driver_identity_encode(response,32,0x102030405060708ULL,0xfedcba9876543210ULL));
assert(wr_iot_driver_identity_decode(&identity,response,32));
assert(identity.adapter_epoch==0x102030405060708ULL&&identity.device_generation==0xfedcba9876543210ULL);
for(unsigned n=0;n<40;n++)if(n!=32){assert(!wr_iot_driver_identity_decode(&identity,response,n));assert(!identity.adapter_epoch&&!identity.device_generation);}
for(unsigned i=0;i<32;i++)if((i>=5&&i<8)||i>=24){response[i]=1;assert(!wr_iot_driver_identity_decode(&identity,response,32));response[i]=0;}
assert(!wr_iot_driver_identity_encode(response,32,0,1));for(unsigned i=0;i<32;i++)assert(!response[i]);
w[3]='1';assert(!wr_iot_driver_open_decode(&r,w,144));w[3]='2';
unsigned char nonce[16]={1},query[32],decoded_nonce[16];
assert(wr_iot_driver_query_encode(query,32,nonce)&&wr_iot_driver_query_decode(decoded_nonce,query,32));
assert(decoded_nonce[0]==1);
query[3]='1';assert(!wr_iot_driver_query_decode(decoded_nonce,query,32));
assert(wr_iot_driver_identity_encode(response,32,1,2));response[3]='1';assert(!wr_iot_driver_identity_decode(&identity,response,32));
assert(!wr_iot_driver_open_decode(&r,0,144));assert(!wr_iot_driver_open_decode(0,w,144));return 0;}
