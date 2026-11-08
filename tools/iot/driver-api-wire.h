/* New RC/driver ABI, owner-authorized 2026-11-08. No ioctl is installed here.
 * Fixed byte record; no native pointers, padding, keys in responses or logs.
 * This decoder establishes syntax only, never an open/lifetime permission. */
#ifndef WR_IOT_DRIVER_API_WIRE_H
#define WR_IOT_DRIVER_API_WIRE_H
#define WR_IOT_DRIVER_IOCTL_OPEN 0x89ff
#define WR_IOT_DRIVER_OPEN_BYTES 144U
struct wr_iot_driver_open_request {
 unsigned long long adapter_epoch,device_generation;
 unsigned char request_id[16];
 unsigned int ssid_length,password_length;
 unsigned char ssid[33],password[65];
};
static inline unsigned long long wr_iot_driver_get64(const unsigned char *p){
 unsigned int i;unsigned long long value=0;
 for(i=0;i<8;i++)value=(value<<8)|p[i];
 return value;
}
static inline void wr_iot_driver_request_wipe(struct wr_iot_driver_open_request *r){
 volatile unsigned char *p=(volatile unsigned char *)r;unsigned int i;
 if(r)for(i=0;i<sizeof(*r);i++)p[i]=0;
}
/* Output is cleared on refusal. Input and output must not overlap. UTF-8,
 * credential derivation and loaded-BSS matching belong to admission, not
 * this transport decoder. Reject embedded NUL and nonzero unused bytes. */
static inline int wr_iot_driver_open_decode(struct wr_iot_driver_open_request *out,
 const unsigned char *wire,unsigned int length){
 struct wr_iot_driver_open_request r={0};unsigned int i,nonzero=0;int valid=0;
 if(!out)return 0;
 wr_iot_driver_request_wipe(out);
 if(!wire||length!=WR_IOT_DRIVER_OPEN_BYTES)goto done;
 if(wire[0]!='W'||wire[1]!='R'||wire[2]!='I'||wire[3]!='1'||wire[4]!=1)goto done;
 for(i=5;i<8;i++)if(wire[i])goto done;
 for(i=42;i<48;i++)if(wire[i])goto done;
 r.adapter_epoch=wr_iot_driver_get64(wire+8);
 r.device_generation=wr_iot_driver_get64(wire+16);
 if(!r.adapter_epoch||!r.device_generation)goto done;
 for(i=0;i<16;i++){r.request_id[i]=wire[24+i];nonzero|=r.request_id[i];}
 if(!nonzero)goto done;
 r.ssid_length=wire[40];r.password_length=wire[41];
 if(!r.ssid_length||r.ssid_length>32||r.password_length<8||r.password_length>64)goto done;
 for(i=0;i<32;i++){
  if(i<r.ssid_length){if(!wire[48+i])goto done;r.ssid[i]=wire[48+i];}
  else if(wire[48+i])goto done;
 }
 for(i=0;i<64;i++){
  if(i<r.password_length){if(!wire[80+i])goto done;r.password[i]=wire[80+i];}
  else if(wire[80+i])goto done;
 }
 *out=r;valid=1;
done:
 wr_iot_driver_request_wipe(&r);return valid;
}
#endif
