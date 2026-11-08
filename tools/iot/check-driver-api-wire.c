#include <assert.h>
#include <string.h>
#include "driver-api-wire.h"
int main(void){unsigned char w[144]={ 'W','R','I','1',1};struct wr_iot_driver_open_request r;
w[15]=1;w[23]=2;w[24]=3;w[40]=3;w[41]=8;memcpy(w+48,"IoT",3);memcpy(w+80,"password",8);
assert(wr_iot_driver_open_decode(&r,w,144));assert(r.adapter_epoch==1&&r.device_generation==2&&!strcmp((char*)r.ssid,"IoT"));
for(unsigned n=0;n<160;n++)if(n!=144){assert(!wr_iot_driver_open_decode(&r,w,n));for(unsigned i=0;i<sizeof r;i++)assert(!((unsigned char*)&r)[i]);}
for(unsigned i=0;i<144;i++)if((i>=5&&i<8)||(i>=42&&i<48)||(i>=51&&i<80)||i>=88){w[i]=1;assert(!wr_iot_driver_open_decode(&r,w,144));w[i]=0;}
for(unsigned i=0;i<256;i++){w[40]=i;assert(wr_iot_driver_open_decode(&r,w,144)==(i==3));}w[40]=3;
for(unsigned i=0;i<256;i++){w[41]=i;assert(wr_iot_driver_open_decode(&r,w,144)==(i==8));}w[41]=8;
assert(!wr_iot_driver_open_decode(&r,0,144));assert(!wr_iot_driver_open_decode(0,w,144));return 0;}
