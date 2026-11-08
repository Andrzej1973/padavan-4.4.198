/* New RC/driver ABI, owner-authorized 2026-11-08. No ioctl is installed here.
 * Fixed byte record; no native pointers, padding, keys in responses or logs.
 * This decoder establishes syntax only, never an open/lifetime permission. */
#ifndef WR_IOT_DRIVER_API_WIRE_H
#define WR_IOT_DRIVER_API_WIRE_H
#define WR_IOT_DRIVER_IOCTL_OPEN 0x89ff
#define WR_IOT_DRIVER_IOCTL_IDENTITY 0x89fe
#define WR_IOT_DRIVER_OPEN_BYTES 144U
#define WR_IOT_DRIVER_IDENTITY_BYTES 32U
struct wr_iot_driver_identity {unsigned long long adapter_epoch,device_generation;};
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
static inline void wr_iot_driver_put64(unsigned char *p,unsigned long long value){
 unsigned int i;for(i=0;i<8;i++){p[7-i]=(unsigned char)value;value>>=8;}
}
static inline int wr_iot_driver_identity_encode(unsigned char *wire,unsigned int length,
 unsigned long long epoch,unsigned long long generation){
 unsigned int i;
 if(!wire||length!=WR_IOT_DRIVER_IDENTITY_BYTES)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!epoch||!generation)return 0;
 wire[0]='W';wire[1]='R';wire[2]='I';wire[3]='1';wire[4]=2;
 wr_iot_driver_put64(wire+8,epoch);wr_iot_driver_put64(wire+16,generation);return 1;
}
/* Observation only. OPEN revalidates both identities under its own owner. */
static inline int wr_iot_driver_identity_decode(struct wr_iot_driver_identity *out,
 const unsigned char *wire,unsigned int length){
 unsigned int i;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=0;
 if(!wire||length!=WR_IOT_DRIVER_IDENTITY_BYTES||wire[0]!='W'||wire[1]!='R'||
    wire[2]!='I'||wire[3]!='1'||wire[4]!=2)return 0;
 for(i=5;i<8;i++)if(wire[i])return 0;
 for(i=24;i<32;i++)if(wire[i])return 0;
 if(!wr_iot_driver_get64(wire+8)||!wr_iot_driver_get64(wire+16))return 0;
 out->adapter_epoch=wr_iot_driver_get64(wire+8);
 out->device_generation=wr_iot_driver_get64(wire+16);return 1;
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
/* Nonoverlapping input/output. Canonical request encoding; decoder remains
 * the shared syntax authority. Security/PMK checks remain driver admission. */
static inline int wr_iot_driver_open_encode(unsigned char *wire,unsigned int length,
 const struct wr_iot_driver_open_request *r){
 struct wr_iot_driver_open_request checked={0};
 unsigned int i;int valid=0;volatile unsigned char *wipe=wire;
 if(!wire||length!=WR_IOT_DRIVER_OPEN_BYTES)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!r||r->ssid_length<1||r->ssid_length>32||r->password_length<8||r->password_length>64)goto done;
 wire[0]='W';wire[1]='R';wire[2]='I';wire[3]='1';wire[4]=1;
 wr_iot_driver_put64(wire+8,r->adapter_epoch);
 wr_iot_driver_put64(wire+16,r->device_generation);
 for(i=0;i<16;i++)wire[24+i]=r->request_id[i];
 wire[40]=(unsigned char)r->ssid_length;wire[41]=(unsigned char)r->password_length;
 for(i=0;i<r->ssid_length;i++)wire[48+i]=r->ssid[i];
 for(i=0;i<r->password_length;i++)wire[80+i]=r->password[i];
 valid=wr_iot_driver_open_decode(&checked,wire,length);
done:
 wr_iot_driver_request_wipe(&checked);
 if(!valid)for(i=0;i<length;i++)wipe[i]=0;
 return valid;
}
#endif
