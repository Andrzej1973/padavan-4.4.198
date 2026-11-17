/* Fixed nonsecret pipe receipt. Native structs/padding never cross the pipe. */
#ifndef WR_IOT_FLASH_WORKER_WIRE_H
#define WR_IOT_FLASH_WORKER_WIRE_H
#include "flash-save-attempt.h"
#include "control-record.h"
#define WR_IOT_FLASH_WORKER_WIRE_BYTES 56
struct wr_iot_flash_worker_receipt {
 char id[33];unsigned long long created,child;
 int mode,phase,attempted,commit_ok;
};
static inline int wr_iot_flash_worker_receipt_valid(const struct wr_iot_flash_worker_receipt *r)
{
 return r&&memchr(r->id,0,sizeof(r->id))&&wr_iot_control_id(r->id)&&r->created&&r->child>1&&
  (r->mode==WR_IOT_FLASH_SAVE_AUTO||r->mode==WR_IOT_FLASH_SAVE_EXPLICIT)&&
  (r->phase==WR_IOT_FLASH_SAVE_UNCERTAIN||r->phase==WR_IOT_FLASH_SAVE_OBSERVED||r->phase==WR_IOT_FLASH_SAVE_MANUAL_PENDING)&&
  (r->attempted==0||r->attempted==1)&&(r->commit_ok==0||r->commit_ok==1)&&
  (!r->commit_ok||r->attempted)&&
  (r->phase!=WR_IOT_FLASH_SAVE_OBSERVED||!r->attempted||r->commit_ok)&&
  (r->phase!=WR_IOT_FLASH_SAVE_MANUAL_PENDING||(!r->attempted&&r->mode==WR_IOT_FLASH_SAVE_AUTO));
}
static inline int wr_iot_flash_worker_receipt_encode(unsigned char *out,size_t size,
 const struct wr_iot_flash_worker_receipt *r)
{
 unsigned char bytes[56]={0};size_t i;
 if(!out||size!=sizeof(bytes)||!wr_iot_flash_worker_receipt_valid(r))return 0;
 memcpy(bytes,"WFS1",4);memcpy(bytes+4,r->id,32);
 for(i=0;i<8;i++){bytes[36+i]=(unsigned char)(r->created>>(56-8*i));bytes[44+i]=(unsigned char)(r->child>>(56-8*i));}
 bytes[52]=r->mode;bytes[53]=r->phase;bytes[54]=r->attempted;bytes[55]=r->commit_ok;
 memcpy(out,bytes,sizeof(bytes));return 1;
}
static inline int wr_iot_flash_worker_receipt_decode(struct wr_iot_flash_worker_receipt *out,
 const unsigned char *bytes,size_t size,const char *id,unsigned long long created,
 unsigned long long child,int mode)
{
 struct wr_iot_flash_worker_receipt r={0};size_t i;
 if(!out||!bytes||size!=56||memcmp(bytes,"WFS1",4)||!id||!wr_iot_control_id(id))return 0;
 memcpy(r.id,bytes+4,32);
 for(i=0;i<8;i++){r.created=(r.created<<8)|bytes[36+i];r.child=(r.child<<8)|bytes[44+i];}
 r.mode=bytes[52];r.phase=bytes[53];r.attempted=bytes[54];r.commit_ok=bytes[55];
 if(!wr_iot_flash_worker_receipt_valid(&r)||strcmp(r.id,id)||r.created!=created||r.child!=child||r.mode!=mode)return 0;
 *out=r;return 1;
}
#endif
