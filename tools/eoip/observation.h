#ifndef WR_EOIP_OBSERVATION_H
#define WR_EOIP_OBSERVATION_H
/* Decode one bounded kernel RTM_NEWLINK observation; no network mutation. */
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <linux/if_link.h>
#include <stdint.h>
#include <string.h>
struct wr_eoip_observation {
 int ifindex;unsigned flags,mtu,master,owned;
 char name[16],kind[16],alias[64];
};
static inline int wr_eoip_attr_string(const unsigned char *p,size_t n,char *out,size_t size)
{
 if(!n||n>size||p[n-1]||memchr(p,0,n-1))return 0;
 memcpy(out,p,n);return 1;
}
static inline int wr_eoip_attrs(const unsigned char *p,size_t size,int nested,struct wr_eoip_observation *out)
{
 unsigned seen=0,count=0;
 while(size){
  struct rtattr header;size_t length,aligned;unsigned type,bit=0;
  if(++count>64||size<sizeof(header))return 0;
  memcpy(&header,p,sizeof(header));length=header.rta_len;
  if(length<RTA_LENGTH(0)||length>size)return 0;
  aligned=RTA_ALIGN(length);if(aligned>size)return 0;
  type=header.rta_type&0x3fff;
  if(nested){if(type==IFLA_INFO_KIND)bit=1;}
  else {
   if(type==IFLA_IFNAME)bit=1;
   else if(type==IFLA_IFALIAS)bit=2;
   else if(type==IFLA_LINKINFO)bit=4;
   else if(type==IFLA_MTU)bit=8;
   else if(type==IFLA_MASTER)bit=16;
  }
  if(bit&&(seen&bit))return 0;
  seen|=bit;
  if(bit){
   const unsigned char *data=p+RTA_LENGTH(0);size_t n=length-RTA_LENGTH(0);
   if(nested){if(!wr_eoip_attr_string(data,n,out->kind,sizeof(out->kind)))return 0;}
   else if(type==IFLA_IFNAME){if(!wr_eoip_attr_string(data,n,out->name,sizeof(out->name)))return 0;}
   else if(type==IFLA_IFALIAS){if(!wr_eoip_attr_string(data,n,out->alias,sizeof(out->alias)))return 0;}
   else if(type==IFLA_LINKINFO){if(!wr_eoip_attrs(data,n,1,out))return 0;}
   else if(n!=sizeof(uint32_t))return 0;
   else if(type==IFLA_MTU)memcpy(&out->mtu,data,sizeof(uint32_t));
   else if(type==IFLA_MASTER)memcpy(&out->master,data,sizeof(uint32_t));
  }
  p+=aligned;size-=aligned;
 }
 return 1;
}
static inline int wr_eoip_decode_link(const void *buffer,size_t size,uint32_t sequence,
 const char *name,const char *owner,struct wr_eoip_observation *out)
{
 struct nlmsghdr message;struct ifinfomsg info;struct wr_eoip_observation value;
 const unsigned char *bytes=buffer;size_t offset=NLMSG_LENGTH(sizeof(info));
 if(!out)return 0;
 memset(out,0,sizeof(*out));memset(&value,0,sizeof(value));
 if(!buffer||!name||!owner||!*name||!*owner||strlen(name)>=sizeof(value.name)||
    strlen(owner)>=sizeof(value.alias)||size<offset||size>4096)return 0;
 memcpy(&message,bytes,sizeof(message));
 if(message.nlmsg_len!=size||message.nlmsg_type!=RTM_NEWLINK||message.nlmsg_seq!=sequence)return 0;
 memcpy(&info,bytes+NLMSG_HDRLEN,sizeof(info));if(info.ifi_index<=0)return 0;
 value.ifindex=info.ifi_index;value.flags=info.ifi_flags;
 if(!wr_eoip_attrs(bytes+offset,size-offset,0,&value)||strcmp(value.name,name))return 0;
 value.owned=!strcmp(value.kind,"eoip")&&!strcmp(value.alias,owner);
 *out=value;return 1;
}
#endif
