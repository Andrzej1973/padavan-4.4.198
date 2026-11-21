#define _GNU_SOURCE
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>
#include <signal.h>
#include "flash-worker.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "native-flash-prepared.h"
#include "config-snapshot-prepared.h"

static int guard(void)
{int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;}
static int owned(const struct wr_iot_flash_worker *s,const char *id,unsigned long long created)
{
 return s&&s->owner==getpid()&&s->self==(uintptr_t)s&&!s->busy&&id&&wr_iot_control_id(id)&&
  memchr(s->id,0,sizeof(s->id))&&!strcmp(s->id,id)&&created&&s->created==created&&
  wr_iot_rc_shutdown.active==1&&guard();
}
static int endpoint(const struct wr_iot_flash_worker *s)
{
 struct stat st;int flags;
 if(s->fd<0||fstat(s->fd,&st)||!S_ISFIFO(st.st_mode)||st.st_dev!=s->pipe_dev||st.st_ino!=s->pipe_ino)return 0;
 flags=fcntl(s->fd,F_GETFL);return flags>=0&&(flags&O_NONBLOCK);
}
static void child_run(struct wr_iot_flash_worker *s,int output)
{
 struct wr_iot_flash_save_attempt attempt={0};struct wr_iot_flash_worker_receipt receipt={0};
 struct sigaction action={0};sigset_t empty;unsigned char wire[56]={0};
 long limit=sysconf(_SC_OPEN_MAX);int fd,sig;ssize_t sent;
 receipt.child=(unsigned long long)getpid();receipt.created=s->created;
 memcpy(receipt.id,s->id,sizeof(receipt.id));receipt.mode=s->mode;receipt.phase=WR_IOT_FLASH_SAVE_UNCERTAIN;
 /* Drop inherited parent status sockets and service-lock descriptors, without
  * calling their owner APIs. Parent retains its original open file descriptions. */
 if(limit<0||limit>1048576)goto report;
 for(fd=0;fd<limit;fd++)if(fd!=output)close(fd);
 action.sa_handler=SIG_DFL;sigemptyset(&action.sa_mask);
 for(sig=1;sig<_NSIG;sig++)if(sig!=SIGKILL&&sig!=SIGSTOP)(void)sigaction(sig,&action,NULL);
 sigemptyset(&empty);if(sigprocmask(SIG_SETMASK,&empty,NULL))goto report;
 if(wr_iot_flash_save_begin(&attempt,s->id,s->created,s->mode,s->expected,strlen(s->expected))){
  receipt.phase=wr_iot_flash_save_step(&attempt,s->id,s->created);
  receipt.attempted=attempt.attempted;receipt.commit_ok=attempt.attempted&&attempt.commit_return==0;
 }
 report:
 /* Every native call and credential cleanup precedes the receipt. No process
  * or command is spawned below; PID1's reaper cannot steal this pipe result. */
 wr_iot_saved_wipe(&attempt,sizeof(attempt));wr_iot_saved_wipe(s,sizeof(*s));
 if(!wr_iot_flash_worker_receipt_encode(wire,sizeof(wire),&receipt))_exit(125);
 do{sent=write(output,wire,sizeof(wire));}while(sent<0&&errno==EINTR);
 close(output);_exit(sent==(ssize_t)sizeof(wire)?0:126);
}
int wr_iot_flash_worker_begin(struct wr_iot_flash_worker *s,const char *id,
 unsigned long long created,enum wr_iot_flash_save_mode mode,const char *expected,size_t length)
{
 struct wr_iot_saved_config checked={0};char canonical[WR_IOT_SAVED_CONFIG_MAX]={0};
 int pipes[2],ok=0;struct stat st;pid_t child;
 if(WR_IOT_NATIVE_FLASH_READBACK_PREPARED!=1||WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED!=1||
    !s||s->owner||s->self||s->child||s->fd||s->created||s->expected[0]||s->spawned||s->phase||s->busy||!id||!wr_iot_control_id(id)||!created||
    (mode!=WR_IOT_FLASH_SAVE_AUTO&&mode!=WR_IOT_FLASH_SAVE_EXPLICIT)||
    wr_iot_rc_shutdown.active!=1||wr_iot_rc_shutdown.pending||!guard()||
    !wr_iot_saved_config_decode(&checked,expected,length)||
    !wr_iot_saved_config_encode(canonical,sizeof(canonical),&checked)||
    strlen(canonical)!=length||memcmp(canonical,expected,length))goto done;
 if(pipe2(pipes,O_NONBLOCK|O_CLOEXEC))goto done;
 if(fstat(pipes[0],&st)||!S_ISFIFO(st.st_mode)){close(pipes[0]);close(pipes[1]);goto done;}
 s->owner=getpid();s->self=(uintptr_t)s;memcpy(s->id,id,sizeof(s->id));s->created=created;s->mode=mode;
 memcpy(s->expected,canonical,length+1);s->fd=pipes[0];s->pipe_dev=st.st_dev;s->pipe_ino=st.st_ino;
 s->spawned=1;s->phase=WR_IOT_FLASH_WORKER_RUNNING;
 child=fork();
 if(!child){close(pipes[0]);child_run(s,pipes[1]);_exit(127);}
 close(pipes[1]);
 if(child<0){close(s->fd);s->fd=-1;s->phase=WR_IOT_FLASH_WORKER_NOT_STARTED;goto done;}
 s->child=child;ok=1;
 done:wr_iot_saved_wipe(&checked,sizeof(checked));wr_iot_saved_wipe(canonical,sizeof(canonical));return ok;
}
enum wr_iot_flash_worker_phase wr_iot_flash_worker_step(struct wr_iot_flash_worker *s,
 const char *id,unsigned long long created)
{
 unsigned char wire[56];struct wr_iot_flash_worker_receipt receipt={0};ssize_t count;
 if(!owned(s,id,created))return WR_IOT_FLASH_WORKER_UNKNOWN;
 if(s->phase!=WR_IOT_FLASH_WORKER_RUNNING)return s->phase;
 if(s->child<=1||!endpoint(s)){s->phase=WR_IOT_FLASH_WORKER_UNKNOWN;return s->phase;}
 s->busy=1;count=read(s->fd,wire,sizeof(wire));
 if(count<0&&(errno==EINTR||errno==EAGAIN||errno==EWOULDBLOCK))goto done;
 s->phase=WR_IOT_FLASH_WORKER_UNKNOWN;
 if(wr_iot_flash_worker_receipt_decode(&receipt,wire,count>0?(size_t)count:0,
    s->id,s->created,(unsigned long long)s->child,s->mode)){
  s->receipt=receipt;
  if(receipt.phase==WR_IOT_FLASH_SAVE_UNCERTAIN&&!receipt.attempted)s->phase=WR_IOT_FLASH_WORKER_NOT_STORED;
  if(receipt.phase==WR_IOT_FLASH_SAVE_OBSERVED)s->phase=WR_IOT_FLASH_WORKER_OBSERVED;
  if(receipt.phase==WR_IOT_FLASH_SAVE_MANUAL_PENDING)s->phase=WR_IOT_FLASH_WORKER_MANUAL_PENDING;
 }
 if(close(s->fd))s->phase=WR_IOT_FLASH_WORKER_UNKNOWN;
 s->fd=-1;
 done:s->busy=0;return s->phase;
}
int wr_iot_flash_worker_retire(struct wr_iot_flash_worker *s,const char *id,unsigned long long created)
{
 if(!owned(s,id,created)||s->fd>=0||
    (s->phase!=WR_IOT_FLASH_WORKER_OBSERVED&&s->phase!=WR_IOT_FLASH_WORKER_MANUAL_PENDING&&
     s->phase!=WR_IOT_FLASH_WORKER_NOT_STARTED&&s->phase!=WR_IOT_FLASH_WORKER_NOT_STORED))return 0;
 wr_iot_saved_wipe(s,sizeof(*s));return 1;
}
