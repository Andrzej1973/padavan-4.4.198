#define WR_HANDSHAKE_TOOL "/proc/self/exe"
#include "handshake-worker.h"
#include "handshake-runtime.h"
#include <assert.h>
#define KEY "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
int main(int argc,char **argv)
{
 struct wr_handshake_observation out,before;
 int fd;char descriptor[32];const char *mode;
 if(argc>1){
  if(argc!=4||strcmp(argv[1],"show")||strcmp(argv[3],"latest-handshakes"))return 8;
  mode=getenv("WR_TEST_MODE");
  if(!mode)return 9;
  fd=atoi(getenv("WR_TEST_FD"));
  errno=0;if(fcntl(fd,F_GETFD)!=-1||errno!=EBADF)return 10;
  if(!strcmp(mode,"malformed")){puts("invalid");return 0;}
  if(!strcmp(mode,"empty"))return 0;
  if(!strcmp(mode,"hang")){for(;;)pause();}
  if(strcmp(argv[2],"wg0")&&strcmp(argv[2],"wg1"))return 11;
  puts(KEY "\t950");
  return !strcmp(mode,"failure")?7:0;
 }
 fd=open("/dev/null",O_RDONLY);assert(fd>2);
 snprintf(descriptor,sizeof(descriptor),"%d",fd);
 assert(!setenv("WR_TEST_FD",descriptor,1));
 assert(!setenv("WR_TEST_MODE","success",1));
 assert(wr_handshake_worker_query("wg0",1000,&out));
 assert(out.peers==1&&out.recent==1&&out.youngest_age==50);
 assert(wr_handshake_worker_query("wg1",1000,&out));
 before=out;
 assert(!wr_handshake_worker_query("wg0;reboot",1000,&out));
 assert(!memcmp(&before,&out,sizeof(out)));
 assert(!setenv("WR_TEST_MODE","failure",1));
 assert(!wr_handshake_worker_query("wg0",1000,&out));
 assert(!memcmp(&before,&out,sizeof(out)));
 assert(!setenv("WR_TEST_MODE","malformed",1));
 assert(!wr_handshake_worker_query("wg0",1000,&out));
 assert(!memcmp(&before,&out,sizeof(out)));
 assert(!setenv("WR_TEST_MODE","empty",1));
 assert(wr_handshake_worker_query("wg0",1000,&out)&&out.peers==0);
 {
  struct wr_handshake_runtime runtime;unsigned attempts;
  wr_handshake_runtime_init(&runtime);
  assert(!setenv("WR_TEST_MODE","success",1));
  assert(wr_handshake_runtime_start(&runtime,"wg0",10,1000));
  assert(!wr_handshake_runtime_start(&runtime,"wg1",10,1000));
  for(attempts=0;attempts<1000&&runtime.pid;attempts++){
   wr_handshake_runtime_tick(&runtime,10);usleep(1000);
  }
  assert(!runtime.pid&&runtime.fd==-1&&runtime.cache.has_sample);
  assert(runtime.cache.observation.recent==1);
  assert(!setenv("WR_TEST_MODE","hang",1));
  assert(wr_handshake_runtime_start(&runtime,"wg0",11,1000));
  usleep(20000);
  for(attempts=0;attempts<1000&&runtime.pid;attempts++){
   wr_handshake_runtime_tick(&runtime,14);usleep(1000);
  }
  assert(!runtime.pid&&runtime.fd==-1);
  assert(wr_handshake_cache_get(&runtime.cache,14,30,NULL)==WR_HS_STALE);
  errno=0;assert(waitpid(-1,NULL,WNOHANG)==-1&&errno==ECHILD);
 }
 assert(fcntl(fd,F_GETFD)!=-1);assert(!close(fd));
 puts("PASS handshake utility arguments, descriptor isolation, failed and malformed observations");
 return 0;
}
