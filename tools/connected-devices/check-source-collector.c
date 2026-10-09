#define _GNU_SOURCE
#include "source-collector.h"
#include "snapshot-cache.h"
#include <assert.h>
#include <sys/wait.h>
#include <signal.h>
static struct wr_device_snapshot snapshot;
static struct wr_device_cache cache;
int main(void){char directory[]="/tmp/device-source-XXXXXX",signal;int pipes[2],ready[2],fd,status;pid_t child;FILE *fp;struct wr_device_source_paths paths={"source","networkmap.lock"};
 assert(mkdtemp(directory));assert(!chdir(directory));fp=fopen("source","w");assert(fp);assert(fputs("192.168.1.2,00:11:22:33:44:55,fixture,1,0,0\n",fp)>=0);assert(!fclose(fp));
 fd=open(paths.lock,O_CREAT|O_RDWR,0600);assert(fd>=0);assert(write(fd,"metadata",8)==8);assert(!close(fd));
 assert(wr_device_networkmap_collect(&snapshot,&paths)&&snapshot.count==1);
 fp=fopen(paths.lock,"r");assert(fp);{char metadata[9]={0};assert(fread(metadata,1,8,fp)==8&&!strcmp(metadata,"metadata"));}assert(!fclose(fp));
 assert(wr_device_cache_init(&cache,"source-fixture"));assert(wr_device_cache_get(&cache,0,wr_device_networkmap_collect,&paths)==WR_DEVICE_CURRENT);
 assert(!pipe(pipes)&&!pipe(ready));child=fork();assert(child>=0);
 if(!child){struct flock lock;close(pipes[1]);close(ready[0]);fd=open(paths.lock,O_RDWR);if(fd<0)_exit(2);memset(&lock,0,sizeof(lock));lock.l_type=F_WRLCK;lock.l_whence=SEEK_SET;if(fcntl(fd,F_SETLK,&lock))_exit(3);if(write(ready[1],"r",1)!=1)_exit(4);if(read(pipes[0],&signal,1)!=1)_exit(5);close(fd);_exit(0);}
 close(pipes[0]);close(ready[1]);assert(read(ready[0],&signal,1)==1);close(ready[0]);
 alarm(3);snapshot.count=99;assert(!wr_device_networkmap_collect(&snapshot,&paths)&&snapshot.count==99);alarm(0);
 assert(wr_device_cache_get(&cache,5000,wr_device_networkmap_collect,&paths)==WR_DEVICE_STALE&&cache.snapshot.count==1);
 assert(write(pipes[1],"x",1)==1);close(pipes[1]);assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 assert(wr_device_networkmap_collect(&snapshot,&paths)&&snapshot.count==1);
 assert(wr_device_cache_get(&cache,10000,wr_device_networkmap_collect,&paths)==WR_DEVICE_CURRENT);
 assert(!unlink("source"));assert(!symlink(paths.lock,"source"));snapshot.count=99;assert(!wr_device_networkmap_collect(&snapshot,&paths)&&snapshot.count==99);assert(!unlink("source"));
 assert(!mkfifo("source",0600));alarm(3);assert(!wr_device_networkmap_collect(&snapshot,&paths));alarm(0);assert(!unlink("source"));
 assert(!unlink(paths.lock));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS nonblocking POSIX source lock, busy-cache fallback, unchanged PID metadata, source symlink/FIFO rejection and bounded passive collection");return 0;
}
