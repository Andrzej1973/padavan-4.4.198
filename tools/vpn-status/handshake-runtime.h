#ifndef WR_HANDSHAKE_RUNTIME_H
#define WR_HANDSHAKE_RUNTIME_H
#include "handshake-worker.h"
#include "handshake-cache.h"
struct wr_handshake_packet {int ok;struct wr_handshake_observation observation;};
struct wr_handshake_runtime {
 pid_t pid;int fd,failed,eof;size_t received;uint64_t started;
 unsigned char bytes[sizeof(struct wr_handshake_packet)+1];
 struct wr_handshake_cache cache;
};
static inline void wr_handshake_runtime_init(struct wr_handshake_runtime *r)
{memset(r,0,sizeof(*r));r->fd=-1;}
/* Nonblocking cancellation. Keep ownership until a subsequent tick reaps it. */
static inline void wr_handshake_runtime_cancel(struct wr_handshake_runtime *r)
{
 if(r->pid>0){kill(-r->pid,SIGKILL);kill(r->pid,SIGKILL);r->failed=1;}
 if(r->fd>=0){close(r->fd);r->fd=-1;}
}
static inline int wr_handshake_runtime_start(struct wr_handshake_runtime *r,
 const char *interface,uint64_t monotonic_now,uint64_t wall_now)
{
 int p[2],flags;pid_t child;
 if(r->pid>0||!interface||(strcmp(interface,"wg0")&&strcmp(interface,"wg1")))return 0;
 if(pipe(p))return 0;
 flags=fcntl(p[0],F_GETFL);
 if(flags<0||fcntl(p[0],F_SETFL,flags|O_NONBLOCK)<0){close(p[0]);close(p[1]);return 0;}
 child=fork();
 if(child<0){close(p[0]);close(p[1]);return 0;}
 if(!child){
  struct wr_handshake_packet packet;ssize_t written;size_t offset=0;
  close(p[0]);
  if(setpgid(0,0))_exit(126);
  signal(SIGTERM,SIG_DFL);signal(SIGPIPE,SIG_DFL);signal(SIGCHLD,SIG_DFL);
  memset(&packet,0,sizeof(packet));
  packet.ok=wr_handshake_worker_query(interface,wall_now,&packet.observation);
  while(offset<sizeof(packet)){
   written=write(p[1],((char *)&packet)+offset,sizeof(packet)-offset);
   if(written<0&&errno==EINTR)continue;
   if(written<=0)_exit(126);
   offset+=(size_t)written;
  }
  close(p[1]);_exit(0);
 }
 close(p[1]);
 /* Both sides establish the group so cancellation covers the utility too. */
 if(setpgid(child,child)&&errno!=EACCES&&errno!=ESRCH){
  kill(child,SIGKILL);r->failed=1;
 }else r->failed=0;
 r->pid=child;r->fd=p[0];r->received=0;r->eof=0;r->started=monotonic_now;
 return 1;
}
/* Call from the event loop with monotonic seconds; never wait for a child. */
static inline int wr_handshake_runtime_tick(struct wr_handshake_runtime *r,uint64_t now)
{
 int status;pid_t result;ssize_t n;struct wr_handshake_packet packet;
 if(r->pid<=0)return 0;
 if(!r->failed&&(now<r->started||now-r->started>=3))wr_handshake_runtime_cancel(r);
 if(r->fd>=0&&!r->eof){
  n=read(r->fd,r->bytes+r->received,sizeof(r->bytes)-r->received);
  if(n>0){r->received+=(size_t)n;if(r->received>sizeof(packet))wr_handshake_runtime_cancel(r);}
  else if(!n)r->eof=1;
  else if(errno!=EINTR&&errno!=EAGAIN&&errno!=EWOULDBLOCK)wr_handshake_runtime_cancel(r);
 }
 result=waitpid(r->pid,&status,WNOHANG);
 if(!result||(result<0&&errno==EINTR))return 0;
 /* On exit, all bytes already written are readable without blocking. */
 if(result==r->pid&&!r->failed&&r->fd>=0&&!r->eof){
  n=read(r->fd,r->bytes+r->received,sizeof(r->bytes)-r->received);
  if(n>0)r->received+=(size_t)n;
  else if(n<0)r->failed=1;
 }
 if(result!=r->pid||!WIFEXITED(status)||WEXITSTATUS(status)||r->received!=sizeof(packet))r->failed=1;
 if(!r->failed){memcpy(&packet,r->bytes,sizeof(packet));if(packet.ok!=1)r->failed=1;}
 wr_handshake_cache_publish(&r->cache,now,!r->failed,r->failed?NULL:&packet.observation);
 if(r->fd>=0)close(r->fd);
 r->fd=-1;r->pid=0;
 return 1;
}
#endif
