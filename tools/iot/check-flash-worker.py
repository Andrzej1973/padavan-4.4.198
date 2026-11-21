#!/usr/bin/env python3
"""Actual fork/pipe worker and real service guard; native flash adapters modeled."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
fields=[b'0',b'IoT test',b'password123',b'192.168.50.1',b'255.255.255.0',b'192.168.50.20',b'192.168.50.200']
record='WR-IOT-CONFIG-1:'+':'.join(v.hex() for v in fields)
source=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <string.h>
#include "flash-worker.h"
#include "service-guard.h"
#include "service-lock.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct model {volatile int allow,manual,commits,reads,unknown,bad_receipt,fail_fork,fail_pipe,preflight_fail;} *model;
static volatile sig_atomic_t reaped;
static pid_t fixture_fork(void){if(model->fail_fork){errno=EAGAIN;return -1;}return fork();}
static int fixture_pipe2(int *fds,int flags){if(model->fail_pipe){errno=EMFILE;return -1;}return pipe2(fds,flags);}
static ssize_t fixture_write(int fd,const void *bytes,size_t length){
 return syscall(SYS_write,fd,bytes,model->bad_receipt?length/2:length);
}
#define write fixture_write
#define fork fixture_fork
#define pipe2 fixture_pipe2
#include "flash-worker.c"
#undef write
#undef fork
#undef pipe2

static void reaper(int sig){int saved=errno,status;(void)sig;while(waitpid(-1,&status,WNOHANG)>0)reaped++;errno=saved;}
int wr_iot_flash_save_snapshot(const char *record,int *manual){int i;assert(record&&*record);for(i=0;i<500&&!model->allow;i++)usleep(10000);if(!model->allow||model->preflight_fail)return 0;*manual=model->manual;return 1;}
int wr_iot_flash_save_commit_once(const char *record,size_t length,enum wr_iot_flash_save_mode mode){assert(strlen(record)==length&&(mode==1||mode==2));__sync_fetch_and_add(&model->commits,1);return model->unknown?-1:0;}
enum wr_iot_flash_config_result wr_iot_native_flash_compare(const char *record,size_t length){int n;assert(strlen(record)==length);n=__sync_add_and_fetch(&model->reads,1);return n==1?WR_IOT_FLASH_CONFIG_DIFFERENT:WR_IOT_FLASH_CONFIG_MATCH;}
static const char id[]="0123456789abcdef0123456789abcdef";
static const char expected[]="RECORD";
static enum wr_iot_flash_worker_phase drain(struct wr_iot_flash_worker *s){int i;enum wr_iot_flash_worker_phase p;for(i=0;i<1000;i++){p=wr_iot_flash_worker_step(s,id,9);if(p!=WR_IOT_FLASH_WORKER_RUNNING)return p;usleep(5000);}assert(0);return 0;}
static void wait_reap(int before){int i;for(i=0;i<1000&&reaped==before;i++)usleep(5000);assert(reaped>before);}
int main(void){
 struct wr_iot_flash_worker s={0},copy;struct sigaction action={0};int guard,before,i;
 struct wr_iot_service_lock competitor={-1};
 struct wr_iot_flash_worker_receipt r={0},decoded,bak;unsigned char wire[56],bad[56];
 model=mmap(NULL,sizeof(*model),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);assert(model!=MAP_FAILED);
 guard=wr_iot_service_guard_enter(1);assert(guard==1);wr_iot_rc_shutdown.active=1;
 action.sa_handler=reaper;sigemptyset(&action.sa_mask);assert(!sigaction(SIGCHLD,&action,NULL));
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 0
 assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected))&&!s.owner&&!model->commits);
 wr_iot_service_guard_leave(guard);assert(!munmap((void*)model,sizeof(*model)));return 0;
#endif
 model->fail_pipe=1;assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected))&&!s.owner);model->fail_pipe=0;
 model->fail_fork=1;assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(s.phase==WR_IOT_FLASH_WORKER_NOT_STARTED&&!s.child&&s.fd==-1&&!model->commits);
 assert(wr_iot_flash_worker_retire(&s,id,9));model->fail_fork=0;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected))&&!s.spawned);wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(wr_iot_flash_worker_step(&s,id,9)==WR_IOT_FLASH_WORKER_RUNNING); /* Child blocked at modeled snapshot. */
 assert(!model->commits&&!wr_iot_service_lock_take(&competitor,WR_IOT_SERVICE_LOCK_PATH));
 assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 copy=s;assert(wr_iot_flash_worker_step(&copy,id,9)==WR_IOT_FLASH_WORKER_UNKNOWN);
 assert(wr_iot_flash_worker_step(&s,id,10)==WR_IOT_FLASH_WORKER_UNKNOWN);
 before=reaped;model->allow=1;wr_iot_rc_shutdown.pending=SIGTERM;
 assert(drain(&s)==WR_IOT_FLASH_WORKER_OBSERVED&&model->commits==1&&s.receipt.attempted&&s.receipt.commit_ok);
 wait_reap(before);assert(wr_iot_flash_worker_retire(&s,id,9)&&!s.owner&&!s.expected[0]);wr_iot_rc_shutdown.pending=0;
 memset((void*)model,0,sizeof(*model));model->manual=1;model->allow=1;before=reaped;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(drain(&s)==WR_IOT_FLASH_WORKER_MANUAL_PENDING&&!model->commits);wait_reap(before);assert(wr_iot_flash_worker_retire(&s,id,9));
 memset((void*)model,0,sizeof(*model));model->unknown=1;model->allow=1;before=reaped;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_EXPLICIT,expected,strlen(expected)));
 assert(drain(&s)==WR_IOT_FLASH_WORKER_UNKNOWN&&model->commits==1);wait_reap(before);
 assert(!wr_iot_flash_worker_retire(&s,id,9));assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_EXPLICIT,expected,strlen(expected)));
 assert(wr_iot_flash_worker_step(&s,id,9)==WR_IOT_FLASH_WORKER_UNKNOWN&&model->commits==1);
 /* Isolated test ends this unknown journal only after its actual child is reaped. No production recovery API is implied. */
 wr_iot_saved_wipe(&s,sizeof(s));
 memset((void*)model,0,sizeof(*model));model->preflight_fail=1;model->allow=1;before=reaped;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(drain(&s)==WR_IOT_FLASH_WORKER_NOT_STORED&&!model->commits);wait_reap(before);
 assert(wr_iot_flash_worker_retire(&s,id,9));
 memset((void*)model,0,sizeof(*model));model->bad_receipt=1;model->allow=1;before=reaped;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(drain(&s)==WR_IOT_FLASH_WORKER_UNKNOWN&&model->commits==1);wait_reap(before);
 assert(!wr_iot_flash_worker_retire(&s,id,9));wr_iot_saved_wipe(&s,sizeof(s));
 memset((void*)model,0,sizeof(*model));before=reaped;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 assert(!kill(s.child,SIGKILL));wait_reap(before);
 assert(drain(&s)==WR_IOT_FLASH_WORKER_UNKNOWN&&!model->commits);
 assert(!wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 wr_iot_saved_wipe(&s,sizeof(s));
 memset((void*)model,0,sizeof(*model));before=reaped;
 assert(wr_iot_flash_worker_begin(&s,id,9,WR_IOT_FLASH_SAVE_AUTO,expected,strlen(expected)));
 {int foreign=open("/dev/null",O_RDONLY|O_CLOEXEC);assert(foreign>=0);
  assert(dup2(foreign,s.fd)==s.fd);if(foreign!=s.fd)close(foreign);
  assert(wr_iot_flash_worker_step(&s,id,9)==WR_IOT_FLASH_WORKER_UNKNOWN);
  assert(fcntl(s.fd,F_GETFD)>=0); /* Library never closes a reused foreign fd. */
  close(s.fd);model->allow=1;wait_reap(before);
 }
 wr_iot_saved_wipe(&s,sizeof(s));
 memcpy(r.id,id,sizeof(r.id));r.created=9;r.child=123;r.mode=1;r.phase=WR_IOT_FLASH_SAVE_OBSERVED;r.attempted=1;r.commit_ok=1;
 assert(wr_iot_flash_worker_receipt_encode(wire,sizeof(wire),&r));memset(&decoded,0x5a,sizeof(decoded));bak=decoded;
 for(i=0;i<56;i++){memcpy(bad,wire,56);bad[i]^=0x80;assert(!wr_iot_flash_worker_receipt_decode(&decoded,bad,56,id,9,123,1));assert(!memcmp(&decoded,&bak,sizeof(bak)));}
 assert(!wr_iot_flash_worker_receipt_decode(&decoded,wire,55,id,9,123,1));
 assert(wr_iot_flash_worker_receipt_decode(&decoded,wire,56,id,9,123,1));
 wr_iot_service_guard_leave(guard);assert(!munmap((void*)model,sizeof(*model)));return 0;
}
'''.replace('RECORD',record)
with tempfile.TemporaryDirectory(prefix='wr-flash-worker-') as directory:
 root=Path(directory);cfile=root/'check.c';binary=root/'check';cfile.write_text(source)
 for enabled in (0,1):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined',
  '-fno-pie','-no-pie','-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED='+str(enabled),'-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1',
  '-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'service.lock')+'"','-I'+str(here),
  str(cfile),str(here/'flash-save-attempt.c'),str(here/'service-guard.c'),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=20)
print('PASS actual fork/pipe worker + real guard: capability0/1, nonblocking parent, reaper, shutdown drain, receipt/descriptor loss, malformed binding, pipe/fork failure and retained unknown/no respawn; native flash modeled')
