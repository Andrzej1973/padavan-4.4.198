#define _GNU_SOURCE
#include <sys/ioctl.h>
#include <net/if_arp.h>
#include <errno.h>
static int injected_ioctl(int fd,unsigned long cmd,struct arpreq *req);
#define WR_IOT_ARP_IOCTL injected_ioctl
#include "arp-restore.h"
#include <assert.h>
#include <stdlib.h>
static int fail_at, calls;
static int injected_ioctl(int fd,unsigned long cmd,struct arpreq *req){
 calls++;if(fail_at&&calls==fail_at){errno=EIO;return -1;}
 return ioctl(fd,cmd,req);
}
int main(void){
 struct wr_iot_arp_state saved,generated,current,foreign;struct wr_iot_arp_entry entry;
 char ns[128];const char *parent=getenv("WR_IOT_PARENT_NETNS");ssize_t n;int fd;struct arpreq dynamic;struct sockaddr_in *dip;
 n=readlink("/proc/self/ns/net",ns,sizeof(ns)-1);
 if(geteuid()!=0||!parent||n<0)return 2;
 ns[n]=0;if(!strcmp(ns,parent))return 2;
 fd=socket(AF_INET,SOCK_DGRAM,0);assert(fd>=0);
 memset(&entry,0,sizeof(entry));entry.flags=ATF_COM|ATF_PERM;
 assert(inet_pton(AF_INET,"192.0.2.20",&entry.address)==1);
 memcpy(entry.mac,"\x02\x11\x22\x33\x44\x55",6);
 assert(wr_iot_arp_write(fd,"br0",&entry,0));assert(wr_iot_arp_capture("br0",&saved));assert(saved.count==1);
 memset(&dynamic,0,sizeof(dynamic));dip=(struct sockaddr_in *)&dynamic.arp_pa;dip->sin_family=AF_INET;
 assert(inet_pton(AF_INET,"192.0.2.40",&dip->sin_addr)==1);
 dynamic.arp_ha.sa_family=ARPHRD_ETHER;memcpy(dynamic.arp_ha.sa_data,"\x02\x11\x22\x33\x44\x88",6);
 dynamic.arp_flags=ATF_COM;strcpy(dynamic.arp_dev,"br0");assert(!ioctl(fd,SIOCSARP,&dynamic));
 assert(inet_pton(AF_INET,"198.51.100.20",&entry.address)==1);
 assert(wr_iot_arp_write(fd,"br1",&entry,0));assert(wr_iot_arp_capture("br1",&foreign));assert(foreign.count==1);
 assert(wr_iot_arp_write(fd,"br0",&saved.entries[0],1));
 assert(inet_pton(AF_INET,"192.0.2.30",&entry.address)==1);entry.mac[5]=0x66;
 assert(wr_iot_arp_write(fd,"br0",&entry,0));assert(wr_iot_arp_capture("br0",&generated));assert(generated.count==1);
 calls=0;fail_at=2;assert(!wr_iot_arp_recover(&saved,&generated));assert(generated.count==0);
 fail_at=0;assert(wr_iot_arp_recover(&saved,&generated));assert(wr_iot_arp_capture("br0",&current));assert(wr_iot_arp_same(&saved,&current));
 assert(!ioctl(fd,SIOCGARP,&dynamic));assert(!(dynamic.arp_flags&ATF_PERM));assert((unsigned char)dynamic.arp_ha.sa_data[5]==0x88);
 assert(wr_iot_arp_capture("br1",&current));assert(wr_iot_arp_same(&foreign,&current));
 /* A caller must not overwrite changes made since its generated snapshot. */
 entry=saved.entries[0];entry.mac[5]=0x77;assert(wr_iot_arp_write(fd,"br0",&entry,0));
 assert(!wr_iot_arp_restore(&saved,&saved));assert(wr_iot_arp_capture("br0",&current));assert(current.count==1&&current.entries[0].mac[5]==0x77);
 assert(!close(fd));
 puts("PASS actual permanent LAN ARP restore in private NET namespace; partial ioctl failure retried, dynamic LAN and other interface preserved and foreign LAN change rejected; RC binding pending");return 0;
}
