/* Snapshot only permanent Ethernet ARP entries on the selected LAN interface. */
#ifndef WR_IOT_ARP_STATE_H
#define WR_IOT_ARP_STATE_H
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <net/if_arp.h>
#define WR_IOT_ARP_MAX 128
struct wr_iot_arp_entry {struct in_addr address;unsigned char mac[6];unsigned int flags;};
struct wr_iot_arp_state {char interface[IFNAMSIZ];size_t count;struct wr_iot_arp_entry entries[WR_IOT_ARP_MAX];};
static inline int wr_iot_arp_stream(FILE *fp,const char *interface,struct wr_iot_arp_state *out){
 struct wr_iot_arp_state candidate;char line[512];size_t n,i;
 if(!fp||!out||!interface||!(n=strlen(interface))||n>=IFNAMSIZ)return 0;
 memset(&candidate,0,sizeof(candidate));memcpy(candidate.interface,interface,n+1);
 if(!fgets(line,sizeof(line),fp)||!strstr(line,"IP address")||!strstr(line,"Device"))return 0;
 while(fgets(line,sizeof(line),fp)){
  char ip[16],mac[18],mask[32],device[IFNAMSIZ],extra;unsigned int type,flags,bytes[6];int consumed=0;
  struct wr_iot_arp_entry entry;
  if(!strchr(line,'\n')&&!feof(fp))return 0;
  if(sscanf(line,"%15s %x %x %17s %31s %15s %c",ip,&type,&flags,mac,mask,device,&extra)!=6)return 0;
  if(strcmp(device,interface)||!(flags&ATF_PERM))continue;
  if(type!=ARPHRD_ETHER||!(flags&ATF_COM)||candidate.count==WR_IOT_ARP_MAX||
     inet_pton(AF_INET,ip,&entry.address)!=1||
     sscanf(mac,"%2x:%2x:%2x:%2x:%2x:%2x%n",&bytes[0],&bytes[1],&bytes[2],&bytes[3],&bytes[4],&bytes[5],&consumed)!=6||
     consumed!=17||strlen(mac)!=17)return 0;
  for(i=0;i<6;i++){if(bytes[i]>255)return 0;entry.mac[i]=(unsigned char)bytes[i];}
  entry.flags=flags;
  for(i=0;i<candidate.count;i++)if(candidate.entries[i].address.s_addr==entry.address.s_addr)return 0;
  candidate.entries[candidate.count++]=entry;
 }
 if(ferror(fp))return 0;
 *out=candidate;return 1;
}
static inline int wr_iot_arp_capture(const char *interface,struct wr_iot_arp_state *out){
 struct wr_iot_arp_state candidate;FILE *fp=fopen("/proc/net/arp","r");int ok;
 if(!fp)return 0;
 ok=wr_iot_arp_stream(fp,interface,&candidate);if(fclose(fp))ok=0;
 if(ok)*out=candidate;return ok;
}
#endif
