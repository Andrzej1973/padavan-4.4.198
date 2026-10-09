#define _GNU_SOURCE
#include <sys/ioctl.h>
#include <net/if_arp.h>
#include <errno.h>
static int injected_ioctl(int fd,unsigned long cmd,struct arpreq *req);
#define WR_IOT_ARP_IOCTL injected_ioctl
#define WR_IOT_DNSMASQ_FIXTURE_ROOT "."
#include "service-state.h"
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
 {
  struct wr_iot_service_state state;struct wr_iot_uts_state old_uts,now;
  char directory[]="/tmp/iot-service-state-XXXXXX",text[32],utsns[128];FILE *fp;const char *utsparent=getenv("WR_IOT_PARENT_UTSNS");
  n=readlink("/proc/self/ns/uts",utsns,sizeof(utsns)-1);assert(utsparent&&n>=0);utsns[n]=0;assert(strcmp(utsns,utsparent));
  assert(mkdtemp(directory));assert(!chdir(directory));assert(!mkdir("etc",0700));assert(!mkdir("etc/dnsmasq",0700));assert(!mkdir("etc/dnsmasq/dhcp",0700));assert(!mkdir("tmp",0700));
  fp=fopen("etc/dnsmasq.conf","w");assert(fp);assert(fputs("previous\n",fp)>=0);assert(!fclose(fp));
  wr_iot_service_state_init(&state);assert(wr_iot_uts_capture(&old_uts));assert(wr_iot_service_guard_enter(1)==1);assert(wr_iot_service_state_begin_guarded(&state,"service.lock","br0"));
  fp=fopen("etc/dnsmasq.conf","w");assert(fp);assert(fputs("candidate\n",fp)>=0);assert(!fclose(fp));
  assert(!sethostname("iot-candidate",13));assert(!setdomainname("candidate.invalid",17));
  assert(wr_iot_service_state_seal(&state,"service.lock"));
  assert(!sethostname("foreign-writer",14));
  assert(!wr_iot_service_state_recover(&state,"service.lock"));
  assert(!wr_iot_service_state_finish(&state,"service.lock"));assert(state.transaction.active&&state.transaction.lock.fd>=0);
  /* Simulate the foreign writer undoing its own change before recovery retry. */
  assert(!sethostname("iot-candidate",13));assert(wr_iot_service_state_recover(&state,"service.lock"));
  assert(wr_iot_uts_capture(&now));assert(!strcmp(old_uts.hostname,now.hostname)&&!strcmp(old_uts.domain,now.domain));
  fp=fopen("etc/dnsmasq.conf","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"previous\n"));assert(!fclose(fp));
  assert(wr_iot_service_state_finish(&state,"service.lock"));wr_iot_service_guard_leave(1);
  /* Failure before final seal: restore known files while retaining an unfinished
   * owned kernel mutation, then recover after its result is captured. */
  wr_iot_service_state_init(&state);assert(wr_iot_service_guard_enter(1)==1);
  assert(wr_iot_service_state_begin_guarded(&state,"service.lock","br0"));
  assert(wr_iot_service_state_track(&state,"service.lock"));
  assert(wr_iot_bundle_write_begin(&state.transaction.files,0));
  fp=fopen("etc/dnsmasq.conf","w");assert(fp);assert(fputs("early-candidate\n",fp)>=0);assert(!fclose(fp));
  assert(wr_iot_bundle_write_end(&state.transaction.files,0));
  assert(wr_iot_service_state_kernel_begin(&state,"service.lock"));
  assert(!sethostname("partial-owned",13));
  assert(!wr_iot_service_state_seal(&state,"service.lock"));
  assert(!wr_iot_service_state_recover(&state,"service.lock"));
  assert(!wr_iot_service_state_finish(&state,"service.lock"));
  fp=fopen("etc/dnsmasq.conf","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"previous\n"));assert(!fclose(fp));
  assert(wr_iot_uts_capture(&now));assert(!strcmp(now.hostname,"partial-owned"));
  assert(wr_iot_service_state_kernel_end(&state,"service.lock"));
  assert(wr_iot_service_state_recover(&state,"service.lock"));
  assert(wr_iot_uts_capture(&now));assert(!strcmp(old_uts.hostname,now.hostname)&&!strcmp(old_uts.domain,now.domain));
  assert(wr_iot_service_state_finish(&state,"service.lock"));wr_iot_service_guard_leave(1);
  assert(!unlink("service.lock"));assert(!unlink("etc/dnsmasq.conf"));assert(!rmdir("etc/dnsmasq/dhcp"));assert(!rmdir("etc/dnsmasq"));assert(!rmdir("etc"));assert(!rmdir("tmp"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 }

 puts("PASS actual permanent LAN ARP restore in private NET namespace; partial ioctl failure retried, dynamic LAN and other interface preserved and foreign LAN change rejected; RC binding pending");return 0;
}
