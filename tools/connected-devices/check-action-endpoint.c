#define _GNU_SOURCE
#include "action-endpoint.h"
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
int main(void){char dir[]="/tmp/action-endpoint-XXXXXX",path[108],lock[114];struct wr_action_endpoint a,b;struct stat st;
 assert(mkdtemp(dir));assert(!chmod(dir,0700));assert(snprintf(path,sizeof(path),"%s/events",dir)>0);assert(snprintf(lock,sizeof(lock),"%s.lock",path)>0);
 assert(!wr_action_endpoint_open(&a,path));assert(wr_action_endpoint_open(&b,path)==-1);assert(!lstat(path,&st)&&S_ISSOCK(st.st_mode));wr_action_endpoint_close(&a);assert(lstat(path,&st)==-1&&errno==ENOENT);
 assert(!wr_action_endpoint_open(&a,path));wr_action_endpoint_close(&a);assert(!unlink(lock));assert(!symlink("missing",path));assert(wr_action_endpoint_open(&a,path)==-1);assert(!lstat(path,&st)&&S_ISLNK(st.st_mode));assert(!unlink(path));assert(!unlink(lock));assert(!rmdir(dir));
 puts("PASS exclusive endpoint ownership, restart, inode cleanup and symlink rejection");return 0;}
