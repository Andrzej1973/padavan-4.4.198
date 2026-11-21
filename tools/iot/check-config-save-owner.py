#!/usr/bin/env python3
"""Compose actual RAM owner/store/guard/parser and actual fork/pipe save worker."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent;shared=here.parent/'band-steering'
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include "config-save-owner.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct model {char record[384];volatile int present,writes,commits,flash_reads,allow,manual,unknown;
 int read_error,epoch,set_unknown,pending_after_set;} *m;
static volatile sig_atomic_t reaped;
static void reaper(int sig){int status,saved=errno;(void)sig;while(waitpid(-1,&status,WNOHANG)>0)reaped++;errno=saved;}
int nvram_getall(char *out,int size,int temporary){
 assert(size==0x20000&&temporary==1);if(m->read_error)return -1;
 memset(out,0,size);if(m->present)snprintf(out,size,"%s=%s",WR_IOT_SAVED_CONFIG_KEY,m->record);return 0;
}
int nvram_set(const char *key,const char *value){
 assert(!strcmp(key,WR_IOT_SAVED_CONFIG_KEY));m->writes++;strcpy(m->record,value);m->present=1;
 if(m->pending_after_set)wr_iot_rc_shutdown.pending=SIGTERM;
 return m->set_unknown?-1:0;
}
int wr_iot_rc_config_backend_capture(struct wr_iot_config_backend *out){
 int fd=wr_iot_service_guard_dup();if(fd<0)return 0;close(fd);
 out->kind=WR_IOT_CONFIG_BACKEND_ACTIVE;strcpy(out->id,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");out->created=m->epoch;return 1;
}
int wr_iot_rc_config_backend_current(const struct wr_iot_config_backend *before){
 int fd=wr_iot_service_guard_dup();if(fd<0)return 0;close(fd);
 return before->kind==WR_IOT_CONFIG_BACKEND_ACTIVE&&before->created==(unsigned)m->epoch;
}
int wr_iot_flash_save_snapshot(const char *expected,int *manual){
 int i;for(i=0;i<500&&!m->allow;i++)usleep(10000);
 if(!m->allow||m->read_error||!m->present||strcmp(expected,m->record))return 0;
 *manual=m->manual;return 1;
}
int wr_iot_flash_save_commit_once(const char *expected,size_t length,enum wr_iot_flash_save_mode mode){
 assert(strlen(expected)==length&&(mode==1||mode==2));__sync_fetch_and_add(&m->commits,1);return m->unknown?-1:0;
}
enum wr_iot_flash_config_result wr_iot_native_flash_compare(const char *expected,size_t length){
 int n;assert(strlen(expected)==length);n=__sync_add_and_fetch(&m->flash_reads,1);return n==1?WR_IOT_FLASH_CONFIG_DIFFERENT:WR_IOT_FLASH_CONFIG_MATCH;
}
static const char id[]="0123456789abcdef0123456789abcdef";
static struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="Save test IoT",.password="password123",
 .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
static void reset(void){
 assert(wr_iot_service_guard_dup()<0);memset((void*)m,0,sizeof(*m));m->epoch=10;
 memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.normal_route_armed=1;
}
static enum wr_iot_config_save_phase drain(struct wr_iot_config_save_owner *s){
 int i;enum wr_iot_config_save_phase phase;
 for(i=0;i<1000;i++){phase=wr_iot_config_save_step(s,id,9,0);if(phase==WR_IOT_CONFIG_SAVE_FLASH||phase==WR_IOT_CONFIG_SAVE_RAM_ONLY)return phase;usleep(5000);}
 assert(0);return 0;
}
static void wait_reap(int before){int i;for(i=0;i<1000&&reaped==before;i++)usleep(5000);assert(reaped>before);}
int main(void){
 struct wr_iot_config_save_owner s={0},copy;struct sigaction action={0};int before,i;
 char expected[384],foreign[384];struct wr_iot_saved_config other=config;
 m=mmap(NULL,sizeof(*m),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);assert(m!=MAP_FAILED);
 action.sa_handler=reaper;sigemptyset(&action.sa_mask);assert(!sigaction(SIGCHLD,&action,NULL));reset();
 assert(wr_iot_saved_config_encode(expected,sizeof(expected),&config));strcpy(other.profile.ssid,"foreign");assert(wr_iot_saved_config_encode(foreign,sizeof(foreign),&other));
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 0
 assert(!wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,&config)&&!s.owner&&!m->writes);
 munmap((void*)m,sizeof(*m));return 0;
#endif
 assert(wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,&config));copy=s;
 assert(wr_iot_config_save_step(&copy,id,9,0)==WR_IOT_CONFIG_SAVE_RECOVERY&&!m->writes);
 assert(wr_iot_config_save_step(&s,id,10,0)==WR_IOT_CONFIG_SAVE_RECOVERY&&!m->writes);
 assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_SAVING&&m->writes==1&&!m->commits);
 before=reaped;m->epoch=11;assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_RECOVERY);m->allow=1;wait_reap(before);
 assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_RECOVERY&&m->commits==1);
 m->epoch=10;assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_FLASH);
 strcpy(m->record,foreign);assert(!wr_iot_config_save_terminal_ready(&s,id,9)&&!s.finished&&m->writes==1&&m->commits==1);
 strcpy(m->record,expected);assert(wr_iot_config_save_terminal_ready(&s,id,9)&&s.finished&&wr_iot_service_guard_dup()<0);
 for(i=0;i<5;i++)assert(wr_iot_config_save_terminal_ready(&s,id,9)&&m->writes==1&&m->commits==1);
 m->epoch=11;assert(!wr_iot_config_save_terminal_ready(&s,id,9));m->epoch=10;
 assert(wr_iot_config_save_terminal_ready(&s,id,9));strcpy(m->record,foreign);assert(!wr_iot_config_save_observed(&s,id,9));
 strcpy(m->record,expected);assert(wr_iot_config_save_observed(&s,id,9)&&wr_iot_rc_shutdown.active==1);
 assert(wr_iot_config_save_retire(&s)&&!s.owner&&!s.ram.expected[0]);
 reset();m->manual=1;m->allow=1;before=reaped;
 assert(wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,&config));assert(drain(&s)==WR_IOT_CONFIG_SAVE_RAM_ONLY);
 wait_reap(before);assert(s.reason==WR_IOT_CONFIG_SAVE_MANUAL_POLICY&&!m->commits&&m->writes==1);
 assert(wr_iot_config_save_terminal_ready(&s,id,9)&&wr_iot_config_save_retire(&s));
 reset();
 assert(wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,&config));
 assert(wr_iot_config_save_step(&s,id,9,1)==WR_IOT_CONFIG_SAVE_REJECTED&&!m->writes&&!s.worker.owner);
 assert(wr_iot_config_save_terminal_ready(&s,id,9)&&wr_iot_config_save_retire(&s));
 reset();m->pending_after_set=1;
 assert(wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,&config));
 assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_RAM_ONLY&&s.reason==WR_IOT_CONFIG_SAVE_CANCELLED&&!s.worker.owner&&!m->commits);
 assert(wr_iot_config_save_terminal_ready(&s,id,9)&&wr_iot_rc_shutdown.pending==SIGTERM);assert(wr_iot_config_save_retire(&s));
 reset();m->manual=1;m->allow=1;m->set_unknown=1;before=reaped;
 assert(wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_EXPLICIT,&config));assert(drain(&s)==WR_IOT_CONFIG_SAVE_FLASH);
 wait_reap(before);assert(m->writes==1&&m->commits==1&&wr_iot_config_save_terminal_ready(&s,id,9));assert(wr_iot_config_save_retire(&s));
 reset();m->allow=1;m->unknown=1;before=reaped;
 assert(wr_iot_config_save_begin_admitted(&s,id,9,WR_IOT_FLASH_SAVE_EXPLICIT,&config));
 assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_SAVING);wait_reap(before);
 assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_RECOVERY&&m->writes==1&&m->commits==1);
 assert(!wr_iot_config_save_terminal_ready(&s,id,9)&&!wr_iot_config_save_retire(&s));
 for(i=0;i<5;i++)assert(wr_iot_config_save_step(&s,id,9,0)==WR_IOT_CONFIG_SAVE_RECOVERY&&m->writes==1&&m->commits==1);
 /* Unknown journal deliberately remains owned until this isolated test process exits. */
 munmap((void*)m,sizeof(*m));return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-config-save-owner-') as directory:
 root=Path(directory);cfile=root/'check.c';binary=root/'check';cfile.write_text(body)
 (root/'rc.h').write_text('int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 for enabled in (0,1):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
  '-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED='+str(enabled),'-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1',
  '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
  '-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'service.lock')+'"','-I'+str(root),'-I'+str(here),
  str(cfile),*[str(here/(unit+'.c')) for unit in ('config-save-owner','config-owner','saved-config-store','flash-worker','flash-save-attempt','service-guard')],
  str(shared/'settings-snapshot.c'),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=25)
print('PASS actual composed save facade + RAM owner/store/parser/guard/fork worker: capability0/1, identity/drift, manual/explicit/cancel, unknown SET/COMMIT, publication retries and no replay; SDK/flash actors')
