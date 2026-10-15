#ifndef WR_EOIP_CONFIG_H
#define WR_EOIP_CONFIG_H
/* Requested configuration only. Validation does not establish tunnel liveness. */
#include <arpa/inet.h>
#include <stdint.h>
#include <string.h>
#define WR_EOIP_SLOTS 8
/* eoip_if_change_mtu: 0xFFF8 - Ethernet header (14) - IPv4/EoIP headers (28). */
#define WR_EOIP_MAX_MTU (0xFFF8U-14U-28U)
struct wr_eoip_config {
 unsigned slot,enabled,autostart,tunnel_id,mtu,keepalive,retries;
 struct in_addr local,remote;
 char bridge[16];
};
static inline int wr_eoip_decimal(const char *s,unsigned maximum,unsigned *out)
{
 unsigned n=0;size_t i,length;
 if(!s||!out||(length=strlen(s))==0||length>10)return 0;
 for(i=0;i<length;i++){
  unsigned digit=(unsigned char)s[i]-'0';
  if(digit>9||digit>maximum||n>(maximum-digit)/10)return 0;
  n=n*10+digit;
 }
 *out=n;return 1;
}
static inline int wr_eoip_ipv4(const char *s,int automatic,struct in_addr *out)
{
 uint32_t host;
 if(!s||inet_pton(AF_INET,s,out)!=1)return 0;
 host=ntohl(out->s_addr);
 if(!host)return automatic;
 /* Reject unspecified, loopback, multicast and reserved/broadcast ranges. */
 return (host>>24)!=0&&(host>>24)!=127&&(host>>24)<224;
}
static inline int wr_eoip_validate(const char *slot,const char *enabled,const char *autostart,
 const char *local,const char *remote,const char *id,const char *mtu,
 const char *keepalive,const char *retries,const char *bridge,struct wr_eoip_config *out)
{
 struct wr_eoip_config value;size_t length;
 if(!out)return 0;
 memset(out,0,sizeof(*out));memset(&value,0,sizeof(value));
 if(!wr_eoip_decimal(slot,WR_EOIP_SLOTS-1,&value.slot)||
    !wr_eoip_decimal(enabled,1,&value.enabled)||!wr_eoip_decimal(autostart,1,&value.autostart)||
    !wr_eoip_ipv4(local,1,&value.local)||!wr_eoip_ipv4(remote,0,&value.remote)||
    (value.local.s_addr&&value.local.s_addr==value.remote.s_addr)||
    !wr_eoip_decimal(id,65535,&value.tunnel_id)||
    !wr_eoip_decimal(mtu,WR_EOIP_MAX_MTU,&value.mtu)||value.mtu<68||
    !wr_eoip_decimal(keepalive,3600,&value.keepalive)||
    !wr_eoip_decimal(retries,255,&value.retries)||!bridge)return 0;
 length=strlen(bridge);
 if(length>=sizeof(value.bridge)||
    strspn(bridge,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")!=length||
    !strcmp(bridge,".")||!strcmp(bridge,".."))return 0;
 memcpy(value.bridge,bridge,length+1);
 if(!value.keepalive)value.retries=0;
 *out=value;return 1;
}
#endif
