/* Caller holds the service lock across capture, owned ARP writes and recovery.
 * On partial failure retain both snapshots; never report successful recovery. */
#ifndef WR_IOT_ARP_RESTORE_H
#define WR_IOT_ARP_RESTORE_H
#include "arp-state.h"
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <unistd.h>
#ifndef WR_IOT_ARP_IOCTL
#define WR_IOT_ARP_IOCTL ioctl
#endif
static inline int wr_iot_arp_valid(const struct wr_iot_arp_state *s){
 size_t i,j;
 if(!s||s->count>WR_IOT_ARP_MAX||!memchr(s->interface,0,IFNAMSIZ)||!s->interface[0])return 0;
 for(i=0;i<s->count;i++){
  if((s->entries[i].flags&(ATF_PERM|ATF_COM))!=(ATF_PERM|ATF_COM)||s->entries[i].flags&~(ATF_PERM|ATF_COM))return 0;
  for(j=0;j<i;j++)if(s->entries[i].address.s_addr==s->entries[j].address.s_addr)return 0;
 }
 return 1;
}
static inline int wr_iot_arp_same(const struct wr_iot_arp_state *a,const struct wr_iot_arp_state *b){
 size_t i,j;
 if(!a||!b||a->count>WR_IOT_ARP_MAX||b->count>WR_IOT_ARP_MAX||
    !memchr(a->interface,0,IFNAMSIZ)||!memchr(b->interface,0,IFNAMSIZ)||
    strcmp(a->interface,b->interface)||a->count!=b->count)return 0;
 for(i=0;i<a->count;i++){
  for(j=0;j<b->count;j++)if(a->entries[i].address.s_addr==b->entries[j].address.s_addr)break;
  if(j==b->count||a->entries[i].flags!=b->entries[j].flags||memcmp(a->entries[i].mac,b->entries[j].mac,6))return 0;
 }
 return 1;
}
static inline int wr_iot_arp_write(int fd,const char *interface,const struct wr_iot_arp_entry *entry,int remove){
 struct arpreq req;struct sockaddr_in *ip;size_t n;
 if(fd<0||!interface||!entry||!(n=strnlen(interface,IFNAMSIZ))||n>=IFNAMSIZ||
    !(entry->flags&ATF_PERM)||!(entry->flags&ATF_COM))return 0;
 memset(&req,0,sizeof(req));ip=(struct sockaddr_in *)&req.arp_pa;
 ip->sin_family=AF_INET;ip->sin_addr=entry->address;
 req.arp_ha.sa_family=ARPHRD_ETHER;memcpy(req.arp_ha.sa_data,entry->mac,6);
 req.arp_flags=entry->flags;memcpy(req.arp_dev,interface,n+1);
 return WR_IOT_ARP_IOCTL(fd,remove?SIOCDARP:SIOCSARP,&req)==0;
}
/* Verify the generated state before any write. Dynamic and other-interface
 * entries are outside this snapshot and remain outside this operation. */
/* expected is updated after each successful owned write, enabling a retry
 * after partial failure while still rejecting foreign intervening changes. */
static inline int wr_iot_arp_recover(const struct wr_iot_arp_state *saved,struct wr_iot_arp_state *expected){
 struct wr_iot_arp_state current;size_t i;int fd,ok=1;
 if(!wr_iot_arp_valid(saved)||!wr_iot_arp_valid(expected)||
    strcmp(saved->interface,expected->interface)||
    !wr_iot_arp_capture(expected->interface,&current)||!wr_iot_arp_same(expected,&current))return 0;
 if(wr_iot_arp_same(saved,expected))return 1;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 while(expected->count){
  if(!wr_iot_arp_write(fd,expected->interface,&expected->entries[expected->count-1],1)){ok=0;break;}
  expected->count--;
 }
 if(ok)for(i=0;i<saved->count;i++){
  if(!wr_iot_arp_write(fd,saved->interface,&saved->entries[i],0)){ok=0;break;}
  expected->entries[expected->count++]=saved->entries[i];
 }
 if(close(fd))ok=0;
 if(ok)ok=wr_iot_arp_capture(saved->interface,&current)&&wr_iot_arp_same(saved,&current);
 return ok;
}
static inline int wr_iot_arp_restore(const struct wr_iot_arp_state *saved,const struct wr_iot_arp_state *generated){
 struct wr_iot_arp_state expected;
 if(!generated)return 0;
 expected=*generated;return wr_iot_arp_recover(saved,&expected);
}
#endif
