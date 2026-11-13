#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#define WR_IOT_SERVICE_LOCK_PATH guard_path
static char guard_path[256];
#include "service-guard.c"
static void contender(int expected)
{
 pid_t child=fork();assert(child>=0);
 if(!child){
  int token=wr_iot_service_guard_enter(1);
  assert(token==expected);
  if(token)wr_iot_service_guard_leave(token);
  else assert(wr_iot_service_guard_dup()==-1);
  _exit(0);
 }
 int status;assert(waitpid(child,&status,0)==child);
 assert(WIFEXITED(status)&&WEXITSTATUS(status)==0);
}
int main(void)
{
 char directory[]="/tmp/wr-iot-service-guard-XXXXXX";
 assert(mkdtemp(directory));
 assert(snprintf(guard_path,sizeof(guard_path),"%s/guard",directory)>0);
 assert(wr_iot_service_guard_dup()==-1);
 assert(wr_iot_service_guard_enter(0)==2);
 int first=wr_iot_service_guard_enter(1);assert(first==1);
 assert(wr_iot_service_guard_enter(1)==1);
 contender(0); /* Child drops inherited fd, not the parent's lock. */
 wr_iot_service_guard_leave(2);contender(0);
 wr_iot_service_guard_leave(1);contender(0); /* Nested owner remains. */
 int duplicate=wr_iot_service_guard_dup();assert(duplicate>=0);
 assert(fcntl(duplicate,F_GETFD)&FD_CLOEXEC);
 assert(close(duplicate)==0);contender(0); /* Duplicate close keeps original. */
 wr_iot_service_guard_leave(first);
 assert(wr_iot_service_guard_dup()==-1);
 contender(1); /* Final owner release permits another process. */
 assert(unlink(guard_path)==0&&rmdir(directory)==0);
 puts("PASS actual service guard with real fork/flock: child cannot unlock parent, nested recovery ownership, duplicate CLOEXEC/close, final release; no router mutation");
 return 0;
}
