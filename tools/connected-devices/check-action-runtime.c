#define _GNU_SOURCE
static char directory[128],socket_path[160];
#define WR_ACTION_DIRECTORY directory
#define WR_ACTION_SOCKET socket_path
#define WR_ACTION_OWNER_LOCK "/nonexistent-wr-owner"
#define WR_ACTION_EXECUTABLE "/nonexistent-wr-exe"
#include "action-runtime.h"
#include <assert.h>
int main(void){struct wr_action_runtime r={0};char pattern[]="/tmp/wr-action-runtime-XXXXXX",lock[180];struct stat st;
 assert(mkdtemp(pattern));snprintf(directory,sizeof(directory),"%s/observer",pattern);snprintf(socket_path,sizeof(socket_path),"%s/actions",directory);
 errno=E2BIG;wr_action_runtime_tick_owned(&r,10000,geteuid());assert(errno==E2BIG&&r.endpoint.fd>=0);assert(r.log.gap&&r.log.interruptions==1);assert(!lstat(socket_path,&st)&&S_ISSOCK(st.st_mode));
 assert(!unlink(socket_path));wr_action_runtime_tick_owned(&r,15000,geteuid());assert(r.endpoint.fd>=0&&!lstat(socket_path,&st));assert(r.log.interruptions==1);
 wr_action_runtime_close(&r);assert(lstat(socket_path,&st)<0);wr_action_runtime_tick_owned(&r,1,geteuid());assert(r.endpoint.fd>=0);wr_action_runtime_close(&r);
 snprintf(lock,sizeof(lock),"%s.lock",socket_path);assert(!unlink(lock));assert(!rmdir(directory));assert(!rmdir(pattern));
 puts("PASS socket-loss recovery, controlled close/reopen, backward uptime and errno isolation");return 0;}
