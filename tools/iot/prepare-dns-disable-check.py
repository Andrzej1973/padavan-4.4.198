#!/usr/bin/env python3
"""Extract DNS disable/commit flow; inject service and filesystem observations."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('controller',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
source=a.controller.read_text(encoding='utf-8')
functions=[]
for anchor in ('static int wr_iot_restart_disable_ready(void)',
               'static int wr_iot_dns_activation_ready(void)',
               'int wr_iot_dns_activation_commit(void)',
               'int wr_iot_dns_disable_prepare(void)',
               'int wr_iot_dns_disable_commit(void)'):
    if source.count(anchor)!=1:
        raise SystemExit('DNS controller function missing or duplicated: '+anchor)
    start=source.index(anchor)
    functions.append(source[start:source.index('\n}',start)+2])
prefix=r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
static int wr_iot_restart_active,wr_iot_restart_prepared,wr_iot_restart_disabling;
static int guard=1,disabled=1,markers_absent=1,journal_ok=1,lock_ok=1,files_ok=1;
static int bridge_present,bridge_owned,bss_down=1;
static int config_ok=1,service_ok=1,candidate_ok=1,starts,finishes,transaction_error;
static struct {struct {int lock;struct {size_t count;int generated[1];const char *paths[1];} files;} transaction;} wr_iot_restart_state;
#define WR_IOT_DNS_CONFIG_PATH "config"
#define IFNAME_BR "br0"
#define WR_IOT_DISABLE_READY wr_iot_restart_disable_ready
#define WR_IOT_CANDIDATE_READY() candidate_ok
static int wr_iot_service_guard_dup(void){return guard?7:-1;}
static int nvram_match(const char *key,const char *value){assert(key&&!strcmp(value,"0"));return disabled;}
static unsigned int if_nametoindex(const char *name){assert(!strcmp(name,"br-iot"));return bridge_present;}
static int wr_iot_bridge_is_owned(void){return bridge_owned;}
static int wr_iot_bss_is_down(void){return bss_down;}
static int close(int fd){assert(fd==7);return 0;}
static int wr_iot_dns_config_without_owned_iot(const char *path){assert(!strcmp(path,"config"));return markers_absent;}
static int wr_iot_writer_journal_failed(void){return !journal_ok;}
static int wr_iot_service_lock_valid(const int *lock,const char *path){(void)lock;(void)path;return lock_ok;}
#define WR_IOT_SERVICE_LOCK_PATH "lock"
static int wr_iot_generated_matches(const int *file,const char *path){(void)file;(void)path;return files_ok;}
static int wr_iot_dns_config_services_at(const char *path,unsigned int *port,int *dhcp4,unsigned int *dhcp_port){
 assert(!strcmp(path,"config"));*port=53;*dhcp4=1;*dhcp_port=67;return config_ok;
}
static int fixture_gateway(const char *name,char out[16]){assert(!strcmp(name,"br0"));strcpy(out,"192.168.1.1");return 1;}
#define WR_IOT_DHCP_GATEWAY fixture_gateway
static int wr_iot_restart_service_wait(unsigned int port,int dhcp4,unsigned int dhcp_port,const char *address){
 assert(port==53&&dhcp4==1&&dhcp_port==67&&!strcmp(address,"192.168.1.1"));return service_ok;
}
static int wr_iot_restart_transaction_mode(int retain){
 assert(retain==1&&!wr_iot_restart_active);starts++;
 if(transaction_error)return transaction_error;
 wr_iot_restart_active=wr_iot_restart_prepared=1;
 wr_iot_restart_state.transaction.files.count=1;return 0;
}
static int wr_iot_restart_finish(void){
 finishes++;wr_iot_restart_active=wr_iot_restart_prepared=wr_iot_restart_disabling=0;return 1;
}
'''
tests=r'''
int main(void){
 int i;int *observations[]={&markers_absent,&journal_ok,&lock_ok,&files_ok,&config_ok,&service_ok,&candidate_ok};
 guard=0;assert(wr_iot_dns_disable_prepare()==EBUSY&&!starts);
 guard=1;disabled=0;assert(wr_iot_dns_disable_prepare()==EINVAL&&!starts);
 disabled=1;bridge_present=1;
 assert(wr_iot_dns_disable_prepare()==EINVAL&&!starts);
 bridge_owned=1;bss_down=0;assert(wr_iot_dns_disable_prepare()==EINVAL&&!starts);
 bss_down=1;transaction_error=EIO;assert(wr_iot_dns_disable_prepare()==EIO&&starts==1);
 transaction_error=0;starts=0;
 assert(!wr_iot_dns_disable_prepare()&&starts==1&&!finishes);
 assert(wr_iot_restart_active&&wr_iot_restart_prepared&&wr_iot_restart_disabling);
 assert(!wr_iot_dns_disable_prepare()&&starts==1&&!finishes);
 for(i=0;i<7;i++){
  *observations[i]=0;
  assert(wr_iot_dns_disable_prepare()==EIO&&starts==1&&!finishes&&wr_iot_restart_active);
  assert(!wr_iot_dns_disable_commit()&&!finishes);
  *observations[i]=1;
  assert(!wr_iot_dns_disable_prepare()&&starts==1);
 }
 assert(wr_iot_dns_disable_commit()&&finishes==1&&!wr_iot_restart_active);
 assert(!wr_iot_dns_disable_commit()&&finishes==1);
 wr_iot_restart_active=wr_iot_restart_prepared=1;wr_iot_restart_disabling=0;
 assert(wr_iot_dns_disable_prepare()==EBUSY&&starts==1);
 puts("PASS actual DNS disable flow: prepared retry only observes, no repeated generation, retained errors, no startup transaction adoption; service/files injected");
 return 0;
}
'''
a.output.write_text(prefix+'\n'.join(functions)+tests,encoding='utf-8')
print('Prepared actual DNS disable flow fixture with injected observations')
