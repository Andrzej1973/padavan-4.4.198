#include <assert.h>
#include <limits.h>
static char controller[PATH_MAX];
#define WR_USBIP_CONTROLLER controller
#include "job-worker.h"

static void read_result(const char *dir,char *out,size_t size)
{
 char path[PATH_MAX];FILE *fp;
 assert(snprintf(path,sizeof(path),"%s/result",dir)<(int)sizeof(path));
 fp=fopen(path,"r");assert(fp);assert(fgets(out,(int)size,fp));fclose(fp);
}
static void reap(pid_t child)
{
 int status;pid_t result;
 do{result=waitpid(child,&status,0);}while(result<0&&errno==EINTR);
 assert(result==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
}
int main(void)
{
 char dir[]="/tmp/wr-usbip-job-XXXXXX",id[33],second[33],reply[512];
 char path[PATH_MAX];pid_t child,other;FILE *fp;int descriptors[2];
 assert(mkdtemp(dir));
 assert(snprintf(controller,sizeof(controller),"%s/controller",dir)<(int)sizeof(controller));
 fp=fopen(controller,"w");assert(fp);
 fputs("#!/bin/sh\n[ ! -e /proc/self/fd/50 ] || exit 98\n[ \"$2\" = 1-1 ] && [ \"$3\" = 1234 ] && [ \"$4\" = abcd ] || exit 99\nwhile [ ! -f \"${0%/*}/release\" ]; do sleep 0.01; done\n[ \"$1\" = bind ] && exit 0\nexit 7\n",fp);
 assert(fclose(fp)==0&&chmod(controller,0700)==0);
 assert(!wr_usbip_job_start(dir,"bind","../1-1","1234","abcd",id,&child));
 assert(!wr_usbip_job_start(dir,"bind","1-1","1234;id","abcd",id,&child));
 assert(pipe(descriptors)==0&&dup2(descriptors[0],50)==50);
 assert(wr_usbip_job_start(dir,"bind","1-1","1234","abcd",id,&child));
 {int status;assert(waitpid(child,&status,WNOHANG)==0);}
 assert(strlen(id)==32);
 assert(!wr_usbip_job_start(dir,"unbind","1-1","1234","abcd",second,&other));
 read_result(dir,reply,sizeof(reply));assert(strstr(reply,id)&&strstr(reply,"\"state\":1"));
 snprintf(path,sizeof(path),"%s/release",dir);fp=fopen(path,"w");assert(fp&&fclose(fp)==0);
 reap(child);read_result(dir,reply,sizeof(reply));assert(strstr(reply,id)&&strstr(reply,"\"state\":2")&&strstr(reply,"\"code\":0"));
 assert(wr_usbip_job_start(dir,"unbind","1-1","1234","abcd",second,&child));
 assert(strcmp(id,second));reap(child);read_result(dir,reply,sizeof(reply));
 assert(strstr(reply,second)&&strstr(reply,"\"state\":3")&&strstr(reply,"\"code\":7"));
 close(50);close(descriptors[0]);close(descriptors[1]);
 assert(chmod(dir,0777)==0);
 assert(!wr_usbip_job_start(dir,"bind","1-1","1234","abcd",id,&child));
 assert(chmod(dir,0700)==0);
 snprintf(path,sizeof(path),"%s/release",dir);unlink(path);
 snprintf(path,sizeof(path),"%s/result",dir);unlink(path);
 snprintf(path,sizeof(path),"%s/lock",dir);unlink(path);unlink(controller);assert(rmdir(dir)==0);
 puts("PASS USB/IP background job: nonblocking start, one job, identity, result, failure, FD closure, private directory");
 return 0;
}
