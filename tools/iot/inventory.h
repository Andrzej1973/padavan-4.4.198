/* Bounded IPv4 interface inventory. Caller must separately collect routed VPN prefixes. */
#ifndef WR_IOT_INVENTORY_H
#define WR_IOT_INVENTORY_H
#include "types.h"
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#include <unistd.h>
#define WR_IOT_INVENTORY_MAX 16
struct wr_iot_inventory {struct wr_iot_range ranges[WR_IOT_INVENTORY_MAX];size_t count;};
static inline int wr_iot_inventory_add(struct wr_iot_inventory *out,uint32_t address,uint32_t mask) {
 struct wr_iot_range range;uint32_t inverse=~mask;size_t i;
 if(!out||out->count>WR_IOT_INVENTORY_MAX||!mask||(inverse&(inverse+1)))return 0;
 range.first=address&mask;range.last=range.first|inverse;
 for(i=0;i<out->count;i++)if(out->ranges[i].first==range.first&&out->ranges[i].last==range.last)return 1;
 if(out->count==WR_IOT_INVENTORY_MAX)return 0;
 out->ranges[out->count++]=range;return 1;
}
/* Snapshot all UP IPv4 interfaces, including aliases and point-to-point endpoints.
 * ignore_owned_iot is permitted only after a separate positive ownership check.
 * Failure leaves output untouched; no interface or route is modified. */
static inline int wr_iot_inventory_interfaces(struct wr_iot_inventory *out,int ignore_owned_iot) {
 struct ifreq entries[128],request;struct ifconf configuration;
 struct wr_iot_inventory candidate;int fd,ok=0;size_t i,n;
 if(!out)return 0;
 memset(&candidate,0,sizeof(candidate));memset(&configuration,0,sizeof(configuration));
 configuration.ifc_len=sizeof(entries);configuration.ifc_req=entries;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 if(ioctl(fd,SIOCGIFCONF,&configuration)<0||configuration.ifc_len<0||
    (size_t)configuration.ifc_len>=sizeof(entries)||configuration.ifc_len%sizeof(struct ifreq))goto done;
 n=(size_t)configuration.ifc_len/sizeof(struct ifreq);
 for(i=0;i<n;i++) {
  uint32_t address,mask;
  if(entries[i].ifr_addr.sa_family!=AF_INET)continue;
  if(!memchr(entries[i].ifr_name,0,IFNAMSIZ))goto done;
  if(ignore_owned_iot&&!strcmp(entries[i].ifr_name,"br-iot"))continue;
  address=ntohl(((struct sockaddr_in *)&entries[i].ifr_addr)->sin_addr.s_addr);
  if(!address)continue;
  memset(&request,0,sizeof(request));memcpy(request.ifr_name,entries[i].ifr_name,IFNAMSIZ);
  if(ioctl(fd,SIOCGIFFLAGS,&request)<0)goto done;
  if(!(request.ifr_flags&IFF_UP))continue;
  if(ioctl(fd,SIOCGIFNETMASK,&request)<0)goto done;
  mask=ntohl(((struct sockaddr_in *)&request.ifr_netmask)->sin_addr.s_addr);
  if(!wr_iot_inventory_add(&candidate,address,mask))goto done;
  if(ioctl(fd,SIOCGIFFLAGS,&request)<0)goto done;
  if(request.ifr_flags&IFF_POINTOPOINT) {
   if(ioctl(fd,SIOCGIFDSTADDR,&request)<0)goto done;
   address=ntohl(((struct sockaddr_in *)&request.ifr_dstaddr)->sin_addr.s_addr);
   if(address&&!wr_iot_inventory_add(&candidate,address,0xffffffffU))goto done;
  }
 }
 *out=candidate;ok=1;
done:close(fd);return ok;
}
#endif
