/* Pure bounded validation of pinned little-endian native NVRAM bytes.
 * No I/O and no persistence claim. Caller owns immutable input for the call.
 */
#ifndef WR_IOT_FLASH_IMAGE_H
#define WR_IOT_FLASH_IMAGE_H
#include <stddef.h>
#include <stdint.h>
#include <string.h>
static inline uint32_t wr_iot_flash_le32(const unsigned char *p)
{
 return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
/* Reflected vendor CRC8 table polynomial; initial value 0xff, no complement. */
static inline unsigned char wr_iot_flash_crc(unsigned char crc,unsigned char b)
{
 unsigned int i;crc^=b;
 for(i=0;i<8;i++)crc=(unsigned char)((crc>>1)^((crc&1)?0xab:0));
 return crc;
}
/* Capacity is the source-verified NVRAM_SPACE, not whole MTD partition size.
 * This strict admission parser deliberately refuses duplicate native keys.
 */
static inline int wr_iot_flash_image_valid(const void *bytes,size_t available,
 size_t capacity)
{
 const unsigned char *p=bytes;size_t len,i,at,stop,eq,prior,prior_end;
 unsigned char crc=0xff;
 if(!p||available<20||capacity<24||capacity>0x20000)return 0;
 len=wr_iot_flash_le32(p+4);
 if(wr_iot_flash_le32(p)!=0x48534c46||p[9]!=1||len<24||
    len>available||len>capacity||(len&3))return 0;
 for(i=9;i<len;i++)crc=wr_iot_flash_crc(crc,p[i]);
 if(crc!=p[8])return 0;
 for(at=20;at<len&&p[at];at=stop+1){
  for(stop=at;stop<len&&p[stop];stop++);
  if(stop==len)return 0;
  for(eq=at;eq<stop&&p[eq]!='=';eq++);
  if(eq==at||eq==stop)return 0;
  for(prior=20;prior<at;prior=prior_end+1){
   for(prior_end=prior;prior_end<at&&p[prior_end];prior_end++);
   if(prior_end-prior>eq-at&&p[prior+eq-at]=='='&&
      !memcmp(p+prior,p+at,eq-at))return 0;
  }
 }
 if(at==len)return 0;
 for(i=at;i<len;i++)if(p[i])return 0;
 return 1;
}
/* Return 1 only for an exact tuple value, 0 for proven absence, -1 for an
 * invalid image/key or insufficient destination. On 0/-1 output is unchanged.
 * Destination is caller-owned; memmove permits overlap with the input image.
 * An empty native value is found successfully and copied as an empty string.
 */
static inline int wr_iot_flash_image_get(const void *bytes,size_t available,
 size_t capacity,const char *key,char *out,size_t out_size)
{
 const unsigned char *p=bytes;size_t keylen,len,at,end,eq,n;
 if(!key||!out||!out_size||!key[0]||strchr(key,'=')||
    !wr_iot_flash_image_valid(bytes,available,capacity))return -1;
 keylen=strlen(key);len=wr_iot_flash_le32(p+4);
 for(at=20;at<len&&p[at];at=end+1){
  for(end=at;end<len&&p[end];end++);
  for(eq=at;eq<end&&p[eq]!='=';eq++);
  if(eq-at!=keylen||memcmp(p+at,key,keylen))continue;
  n=end-eq-1;
  if(n>=out_size)return -1;
  memmove(out,p+eq+1,n+1);return 1;
 }
 return 0;
}
#endif
