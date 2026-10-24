#define _GNU_SOURCE
#include "control-mailbox.h"
#include <errno.h>
#include <stdlib.h>

static int directory_valid(const struct wr_iot_mailbox *m){
 struct stat held,named;
 return m&&m->directory>=0&&!fstat(m->directory,&held)&&!lstat(m->path,&named)&&
  S_ISDIR(held.st_mode)&&S_ISDIR(named.st_mode)&&held.st_uid==geteuid()&&
  (held.st_mode&07777)==0700&&held.st_dev==named.st_dev&&held.st_ino==named.st_ino;
}
static int valid(const struct wr_iot_mailbox *m){
 return directory_valid(m)&&wr_iot_service_lock_valid(&m->lock,m->lock_path);
}
static int file_valid(int fd,int dir,const char *name,struct stat *out){
 struct stat held,named;
 if(fstat(fd,&held)||fstatat(dir,name,&named,AT_SYMLINK_NOFOLLOW))return 0;
 if(!S_ISREG(held.st_mode)||!S_ISREG(named.st_mode)||held.st_uid!=geteuid()||
    (held.st_mode&07777)!=0600||held.st_nlink!=1||held.st_dev!=named.st_dev||
    held.st_ino!=named.st_ino)return 0;
 if(out)*out=held;
 return 1;
}
void wr_iot_mailbox_init(struct wr_iot_mailbox *m){
 memset(m,0,sizeof(*m));m->directory=-1;m->lock.fd=-1;
}
void wr_iot_mailbox_close(struct wr_iot_mailbox *m){
 if(!m)return;
 wr_iot_service_lock_release(&m->lock);
 if(m->directory>=0)close(m->directory);
 wr_iot_mailbox_init(m);
}
int wr_iot_mailbox_open(struct wr_iot_mailbox *out,const char *path,int create){
 struct wr_iot_mailbox m;int n;
 if(!out||out->directory!=-1||out->lock.fd!=-1||!path||path[0]!='/')return 0;
 wr_iot_mailbox_init(&m);
 n=snprintf(m.path,sizeof(m.path),"%s",path);
 if(n<=0||(size_t)n>=sizeof(m.path))return 0;
 n=snprintf(m.lock_path,sizeof(m.lock_path),"%s/lock",path);
 if(n<=0||(size_t)n>=sizeof(m.lock_path))return 0;
 if(create&&mkdir(path,0700)&&errno!=EEXIST)return 0;
 m.directory=open(path,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(m.directory<0||!directory_valid(&m)||
    !wr_iot_service_lock_take(&m.lock,m.lock_path)||!valid(&m)){
  wr_iot_mailbox_close(&m);return 0;
 }
 *out=m;return 1;
}
/* 1 read, 0 missing, -1 unsafe/error. Never follow a symlink or block on FIFO. */
static int read_record(struct wr_iot_mailbox *m,const char *name,char *out,size_t capacity,size_t *length){
 struct stat before,after;int fd;size_t used=0;ssize_t got;char extra;
 if(!valid(m))return -1;
 fd=openat(m->directory,name,O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);
 if(fd<0)return errno==ENOENT?0:-1;
 if(!file_valid(fd,m->directory,name,&before)||before.st_size<=0||
    (unsigned long long)before.st_size>=capacity)goto fail;
 while(used<(size_t)before.st_size){
  got=read(fd,out+used,(size_t)before.st_size-used);
  if(got<0&&errno==EINTR)continue;
  if(got<=0)goto fail;
  used+=(size_t)got;
 }
 do{got=read(fd,&extra,1);}while(got<0&&errno==EINTR);
 if(got||!file_valid(fd,m->directory,name,&after)||before.st_size!=after.st_size||
    before.st_mtime!=after.st_mtime||before.st_ctime!=after.st_ctime||!valid(m))goto fail;
 if(close(fd))return -1;
 out[used]=0;*length=used;return 1;
 fail:close(fd);return -1;
}
static int write_record(struct wr_iot_mailbox *m,const char *temporary,const char *name,
 const char *data,size_t length){
 int fd,ok=0;size_t used=0;ssize_t written;
 if(!valid(m)||!length)return 0;
 fd=openat(m->directory,temporary,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
 if(fd<0)return 0;
 if(fchmod(fd,0600)||!file_valid(fd,m->directory,temporary,NULL))goto done;
 while(used<length){
  written=write(fd,data+used,length-used);
  if(written<0&&errno==EINTR)continue;
  if(written<=0)goto done;
  used+=(size_t)written;
 }
 if(fsync(fd)||!file_valid(fd,m->directory,temporary,NULL)||!valid(m))goto done;
 if(renameat(m->directory,temporary,m->directory,name))goto done;
 /* After rename, any uncertainty retains the published record. */
 ok=fsync(m->directory)==0;
 done:
 if(!ok&&file_valid(fd,m->directory,temporary,NULL))unlinkat(m->directory,temporary,0);
 if(close(fd))ok=0;
 return ok;
}
static int result_read(struct wr_iot_mailbox *m,struct wr_iot_control_result *out){
 char buffer[160],*lines[5];size_t n,i,start=0,count=0;
 struct wr_iot_control_result r={0};int status=read_record(m,"result",buffer,sizeof(buffer),&n);
 if(status!=1)return status;
 if(memchr(buffer,0,n))return -1;
 for(i=0;i<n;i++)if(buffer[i]=='\n'){
  if(count==5)return -1;
  lines[count++]=buffer+start;buffer[i]=0;start=i+1;
 }
 if(count!=5||start!=n||strcmp(lines[0],"WR-IOT-RESULT-1")||
    !wr_iot_control_id(lines[1])||strlen(lines[2])!=1||lines[2][0]<'1'||lines[2][0]>'5'||
    !wr_iot_control_time(lines[3],&r.created)||!wr_iot_control_time(lines[4],&r.observed)||
    r.created>r.observed)return -1;
 memcpy(r.id,lines[1],33);r.state=(enum wr_iot_result_state)(lines[2][0]-'0');
 *out=r;return 1;
}
static int result_write(struct wr_iot_mailbox *m,const struct wr_iot_control_result *r){
 char buffer[160];int n;
 if(!wr_iot_control_result_current(r,r->id,r->observed,0))return 0;
 n=snprintf(buffer,sizeof(buffer),"WR-IOT-RESULT-1\n%s\n%d\n%llu\n%llu\n",
  r->id,(int)r->state,r->created,r->observed);
 return n>0&&(size_t)n<sizeof(buffer)&&write_record(m,"result.new","result",buffer,(size_t)n);
}
int wr_iot_mailbox_result(struct wr_iot_mailbox *m,struct wr_iot_control_result *out){
 struct wr_iot_control_result r;
 if(!out||result_read(m,&r)!=1)return 0;
 *out=r;return 1;
}
int wr_iot_mailbox_submit(struct wr_iot_mailbox *m,const struct wr_iot_control_request *request){
 struct stat st;struct wr_iot_control_result previous,r={0};char buffer[512];int n,status;
 if(!valid(m)||!request)return 0;
 n=wr_iot_control_encode(buffer,sizeof(buffer),request);
 if(!n)return 0;
 if(!fstatat(m->directory,"request",&st,AT_SYMLINK_NOFOLLOW)||errno!=ENOENT)goto fail;
 status=result_read(m,&previous);
 if(status<0||(status==1&&
    (!strcmp(previous.id,request->id)||previous.observed>request->created||
     (previous.state!=WR_IOT_RESULT_APPLIED&&previous.state!=WR_IOT_RESULT_REJECTED))))goto fail;
 memcpy(r.id,request->id,33);r.created=r.observed=request->created;r.state=WR_IOT_RESULT_QUEUED;
 status=write_record(m,"request.new","request",buffer,(size_t)n);
 memset(buffer,0,sizeof(buffer));
 /* Retain a published request on failed result publication; never execute it
  * without a matching queued result, and never accept a replacement. */
 return status&&result_write(m,&r);
 fail:memset(buffer,0,sizeof(buffer));return 0;
}
static int request_read(struct wr_iot_mailbox *m,struct wr_iot_control_request *out){
 char buffer[512];size_t n;int status=read_record(m,"request",buffer,sizeof(buffer),&n);
 status=status==1?wr_iot_control_decode(out,buffer,n):0;
 memset(buffer,0,sizeof(buffer));return status;
}
int wr_iot_mailbox_finish(struct wr_iot_mailbox *m,const char *id,
 enum wr_iot_result_state next,unsigned long long now){
 struct wr_iot_control_request request={0};struct wr_iot_control_result r;
 if(!wr_iot_control_id(id)||!request_read(m,&request)||strcmp(id,request.id)||
    result_read(m,&r)!=1||strcmp(r.id,id)||r.created!=request.created||now<r.observed)goto fail;
 memset(&request,0,sizeof(request));
 if(next!=WR_IOT_RESULT_APPLIED&&next!=WR_IOT_RESULT_REJECTED&&next!=WR_IOT_RESULT_RECOVERY)return 0;
 if(r.state!=next){
  if(r.state!=WR_IOT_RESULT_RUNNING&&
     !(r.state==WR_IOT_RESULT_QUEUED&&next==WR_IOT_RESULT_REJECTED)&&
     !(r.state==WR_IOT_RESULT_RECOVERY&&next==WR_IOT_RESULT_REJECTED))return 0;
  r.state=next;r.observed=now;
  if(!result_write(m,&r))return 0;
 }else if(next==WR_IOT_RESULT_RECOVERY){
  r.observed=now;return result_write(m,&r);
 }
 if(next==WR_IOT_RESULT_RECOVERY)return 1;
 /* Result is terminal before removing credentials. Failed cleanup can be
  * retried with this same terminal state without executing activation again. */
 return valid(m)&&!unlinkat(m->directory,"request",0)&&!fsync(m->directory);
 fail:memset(&request,0,sizeof(request));return 0;
}
int wr_iot_mailbox_claim(struct wr_iot_mailbox *m,unsigned long long now,
 struct wr_iot_control_request *out){
 struct wr_iot_control_request request={0};struct wr_iot_control_result r;
 if(!out||!request_read(m,&request)||result_read(m,&r)!=1||
    strcmp(request.id,r.id)||request.created!=r.created||r.state!=WR_IOT_RESULT_QUEUED||
    now<r.observed)goto fail;
 if(now-request.created>30){
  wr_iot_mailbox_finish(m,request.id,WR_IOT_RESULT_REJECTED,now);goto fail;
 }
 r.state=WR_IOT_RESULT_RUNNING;r.observed=now;
 if(!result_write(m,&r))goto fail;
 *out=request;memset(&request,0,sizeof(request));return 1;
 fail:memset(&request,0,sizeof(request));return 0;
}
