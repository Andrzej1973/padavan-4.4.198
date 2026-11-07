/* Task-context key derivation under the existing configuration/lifetime owner.
 * Derivation must run outside spinlocks/atomic/IRQ context. Caller retains a
 * task-owned configuration lease and lifetime pin across work and revalidation.
 * No ioctl, firmware operation, mutation or key export. Caller must fence all
 * setters and revalidate its generation/ticket before using this observation. */
#ifndef WR_IOT_PRECREATED_KEY_MATCH_H
#define WR_IOT_PRECREATED_KEY_MATCH_H
#include "precreated-loaded-config.h"
static inline int wr_iot_precreated_key_matches(PRTMP_ADAPTER ad,PNET_DEV dev,
 const unsigned char *ssid,unsigned int ssid_length,const char *password,unsigned int password_length)
{
 unsigned char derived[40]={0};char passphrase[64];
 volatile unsigned char *wipe;unsigned int i;int result=0;
 if(!ad||!dev||!ssid||!password||ssid_length<1||ssid_length>32||password_length<8||password_length>64)return 0;
 if(password_length==64){
  for(i=0;i<64;i++){
   unsigned char c=(unsigned char)password[i];unsigned int nibble;
   if(c>='0'&&c<='9')nibble=c-'0';
   else if(c>='a'&&c<='f')nibble=c-'a'+10;
   else if(c>='A'&&c<='F')nibble=c-'A'+10;
   else goto done;
   derived[i/2]=(unsigned char)((derived[i/2]<<4)|nibble);
  }
 }else{
  for(i=0;i<password_length;i++){
   unsigned char c=(unsigned char)password[i];
   if(c<32||c>126)goto done;
   passphrase[i]=password[i];
  }
  passphrase[password_length]=0;
  if(!RtmpPasswordHash(passphrase,(unsigned char *)ssid,(int)ssid_length,derived))goto done;
 }
 result=wr_iot_precreated_loaded_matches(ad,dev,ssid,ssid_length,derived,32);
 done:
 wipe=derived;for(i=0;i<sizeof(derived);i++)wipe[i]=0;
 wipe=(volatile unsigned char *)passphrase;for(i=0;i<sizeof(passphrase);i++)wipe[i]=0;
 return result;
}
#endif
