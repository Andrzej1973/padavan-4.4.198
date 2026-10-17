#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "runtime-state.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

static int private_fd(int fd,int directory)
{
    struct stat st;
    if (fstat(fd,&st) || st.st_uid!=geteuid()) return 0;
    return directory?(S_ISDIR(st.st_mode) && (st.st_mode&0777)==0700):
        (S_ISREG(st.st_mode) && st.st_nlink==1 && (st.st_mode&0777)==0600);
}
static int valid_session(const struct wr_vpn_session *s)
{
    unsigned int i,nonzero=0;struct wr_vpn_resources r;
    if (!s || !s->revision || s->index>INT_MAX || !wr_vpn_resources_make(&r,s->id,s->protocol)) return 0;
    for (i=0;i<sizeof(s->nonce);i++) nonzero|=s->nonce[i];
    return nonzero!=0;
}
static int same_session(const struct wr_vpn_session *a,const struct wr_vpn_session *b)
{
    return a->id==b->id && a->protocol==b->protocol && a->revision==b->revision &&
        a->index==b->index && !memcmp(a->nonce,b->nonce,sizeof(a->nonce));
}
static int transfer(int fd,void *buffer,size_t size,int writing)
{
    unsigned char *p=buffer;
    while (size) {
        ssize_t n=writing?write(fd,p,size):read(fd,p,size);
        if (n<0 && errno==EINTR) continue;
        if (n<=0) return 0;
        p+=n;size-=(size_t)n;
    }
    return 1;
}
static void encode32(unsigned char *p,uint32_t v)
{ p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v; }
static uint32_t decode32(const unsigned char *p)
{ return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3]; }
static int locked(struct wr_vpn_runtime *r)
{ return r && r->root>=0 && r->lock>=0 && private_fd(r->root,1) && private_fd(r->lock,0); }
enum wr_vpn_runtime_result wr_vpn_runtime_lock(const char *path,struct wr_vpn_runtime *out)
{
    int root,lock;
    if (!path || !out || out->root>=0 || out->lock>=0) return WR_VPN_RUNTIME_INVALID;
    if (mkdir(path,0700) && errno!=EEXIST) return WR_VPN_RUNTIME_IO;
    root=open(path,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (root<0) return WR_VPN_RUNTIME_IO;
    if (!private_fd(root,1)) { close(root);return WR_VPN_RUNTIME_INVALID; }
    lock=openat(root,".operation-lock",O_RDWR|O_CREAT|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK,0600);
    if (lock<0) { close(root);return WR_VPN_RUNTIME_IO; }
    if (!private_fd(lock,0)) { close(lock);close(root);return WR_VPN_RUNTIME_INVALID; }
    if (flock(lock,LOCK_EX|LOCK_NB)) {
        int busy=errno==EWOULDBLOCK || errno==EAGAIN;
        close(lock);close(root);return busy?WR_VPN_RUNTIME_BUSY:WR_VPN_RUNTIME_IO;
    }
    out->root=root;out->lock=lock;return WR_VPN_RUNTIME_OK;
}
void wr_vpn_runtime_unlock(struct wr_vpn_runtime *r)
{
    if (!r) return;
    if (r->lock>=0) close(r->lock);
    if (r->root>=0) close(r->root);
    r->lock=r->root=-1;
}
enum wr_vpn_runtime_result wr_vpn_runtime_read(struct wr_vpn_runtime *r,unsigned int id,struct wr_vpn_session *out)
{
    char name[16];unsigned char data[48];struct stat st;struct wr_vpn_session s;int fd,ok;
    if (!out || !locked(r) || !id || id>WR_VPN_PROFILE_ID_MAX) return WR_VPN_RUNTIME_INVALID;
    snprintf(name,sizeof(name),"%u",id);
    fd=openat(r->root,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd<0) return errno==ENOENT?WR_VPN_RUNTIME_ABSENT:WR_VPN_RUNTIME_IO;
    ok=private_fd(fd,0) && !fstat(fd,&st) && st.st_size==sizeof(data) && transfer(fd,data,sizeof(data),0);
    close(fd);if (!ok) return WR_VPN_RUNTIME_INVALID;
    memset(&s,0,sizeof(s));s.id=decode32(data+8);s.protocol=(enum wr_vpn_protocol)decode32(data+12);
    s.revision=((uint64_t)decode32(data+16)<<32)|decode32(data+20);s.index=decode32(data+24);
    memcpy(s.nonce,data+32,sizeof(s.nonce));
    if (memcmp(data,"WRVS\1\0\0\0",8) || decode32(data+28) || s.id!=id || !valid_session(&s)) return WR_VPN_RUNTIME_INVALID;
    *out=s;return WR_VPN_RUNTIME_OK;
}
enum wr_vpn_runtime_result wr_vpn_runtime_put(struct wr_vpn_runtime *r,const struct wr_vpn_session *s,const struct wr_vpn_session *expected)
{
    char name[16],temp[48];unsigned char data[48];struct wr_vpn_session prior;
    enum wr_vpn_runtime_result status;int fd,ok;
    if (!locked(r) || !valid_session(s) || (expected && (!valid_session(expected) || expected->id!=s->id))) return WR_VPN_RUNTIME_INVALID;
    status=wr_vpn_runtime_read(r,s->id,&prior);
    if (expected) {
        if (status!=WR_VPN_RUNTIME_OK) return status==WR_VPN_RUNTIME_ABSENT?WR_VPN_RUNTIME_STALE:status;
        if (!same_session(&prior,expected)) return WR_VPN_RUNTIME_STALE;
        /* Only the pre-create intent may acquire its observed ifindex. */
        prior.index=s->index;
        if (expected->index || !s->index || !same_session(&prior,s)) return WR_VPN_RUNTIME_INVALID;
    } else if (status!=WR_VPN_RUNTIME_ABSENT) return status==WR_VPN_RUNTIME_OK?WR_VPN_RUNTIME_STALE:status;
    else if (s->index) return WR_VPN_RUNTIME_INVALID;
    memset(data,0,sizeof(data));memcpy(data,"WRVS\1",5);encode32(data+8,s->id);encode32(data+12,s->protocol);
    encode32(data+16,(uint32_t)(s->revision>>32));encode32(data+20,(uint32_t)s->revision);encode32(data+24,s->index);
    memcpy(data+32,s->nonce,sizeof(s->nonce));snprintf(name,sizeof(name),"%u",s->id);
    snprintf(temp,sizeof(temp),".session-%u-%ld",s->id,(long)getpid());
    fd=openat(r->root,temp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if (fd<0) return WR_VPN_RUNTIME_IO;
    ok=!fchmod(fd,0600) && transfer(fd,data,sizeof(data),1);
    if (close(fd)) ok=0;
    if (ok && !renameat(r->root,temp,r->root,name)) return WR_VPN_RUNTIME_OK;
    unlinkat(r->root,temp,0);return WR_VPN_RUNTIME_IO;
}
enum wr_vpn_runtime_result wr_vpn_runtime_clear(struct wr_vpn_runtime *r,const struct wr_vpn_session *expected)
{
    struct wr_vpn_session prior;enum wr_vpn_runtime_result status;char name[16];
    if (!locked(r) || !valid_session(expected)) return WR_VPN_RUNTIME_INVALID;
    status=wr_vpn_runtime_read(r,expected->id,&prior);
    if (status!=WR_VPN_RUNTIME_OK) return status;
    if (!same_session(&prior,expected)) return WR_VPN_RUNTIME_STALE;
    snprintf(name,sizeof(name),"%u",expected->id);
    return unlinkat(r->root,name,0)?WR_VPN_RUNTIME_IO:WR_VPN_RUNTIME_OK;
}
static int valid_record(const struct wr_vpn_record *record)
{
    struct wr_vpn_resources resources;
    return record && record->size && record->size<=WR_VPN_CONFIG_MAX &&
        wr_vpn_resources_make(&resources,record->id,record->protocol);
}
enum wr_vpn_runtime_result wr_vpn_runtime_snapshot_put(struct wr_vpn_runtime *r,
                                                       const struct wr_vpn_record *record)
{
    char name[24],temp[48];unsigned char header[28];int fd,ok;
    if (!locked(r) || !valid_record(record)) return WR_VPN_RUNTIME_INVALID;
    memset(header,0,sizeof(header));memcpy(header,"WRVG\1",5);
    encode32(header+8,record->id);encode32(header+12,record->protocol);
    encode32(header+16,(uint32_t)(record->revision>>32));encode32(header+20,(uint32_t)record->revision);
    encode32(header+24,(uint32_t)record->size);
    snprintf(name,sizeof(name),"snapshot-%u",record->id);
    snprintf(temp,sizeof(temp),".snapshot-%u-%ld",record->id,(long)getpid());
    fd=openat(r->root,temp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if (fd<0) return WR_VPN_RUNTIME_IO;
    ok=!fchmod(fd,0600) && transfer(fd,header,sizeof(header),1) &&
        transfer(fd,(void *)record->config,record->size,1);
    if (close(fd)) ok=0;
    if (ok && !renameat(r->root,temp,r->root,name)) return WR_VPN_RUNTIME_OK;
    unlinkat(r->root,temp,0);return WR_VPN_RUNTIME_IO;
}
enum wr_vpn_runtime_result wr_vpn_runtime_snapshot_get(struct wr_vpn_runtime *r,
                                                       unsigned int id,struct wr_vpn_record *out)
{
    char name[24];unsigned char header[28];struct stat st;int fd,ok;uint32_t size;
    if (!out || !locked(r) || !id || id>WR_VPN_PROFILE_ID_MAX) return WR_VPN_RUNTIME_INVALID;
    snprintf(name,sizeof(name),"snapshot-%u",id);
    fd=openat(r->root,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd<0) return errno==ENOENT?WR_VPN_RUNTIME_ABSENT:WR_VPN_RUNTIME_IO;
    ok=private_fd(fd,0) && !fstat(fd,&st) &&
        st.st_size>=(off_t)sizeof(header) &&
        st.st_size<=(off_t)(sizeof(header)+WR_VPN_CONFIG_MAX) &&
        transfer(fd,header,sizeof(header),0);
    size=ok?decode32(header+24):0;
    if (ok && (memcmp(header,"WRVG\1",5) || decode32(header+8)!=id || !size ||
               size>WR_VPN_CONFIG_MAX || st.st_size!=(off_t)(sizeof(header)+size))) ok=0;
    memset(out,0,sizeof(*out));
    if (ok) {
        out->id=id;out->protocol=(enum wr_vpn_protocol)decode32(header+12);
        out->revision=((uint64_t)decode32(header+16)<<32)|decode32(header+20);
        out->size=size;
        ok=transfer(fd,out->config,size,0) && valid_record(out);
    }
    close(fd);
    return ok?WR_VPN_RUNTIME_OK:WR_VPN_RUNTIME_INVALID;
}
int wr_vpn_session_new(struct wr_vpn_session *out,unsigned int id,enum wr_vpn_protocol protocol,uint64_t revision)
{
    struct wr_vpn_session s;int fd,ok;
    if (!out) return 0;
    memset(&s,0,sizeof(s));s.id=id;s.protocol=protocol;s.revision=revision;
    fd=open("/dev/urandom",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if (fd<0) return 0;
    ok=transfer(fd,s.nonce,sizeof(s.nonce),0);close(fd);
    if (!ok || !valid_session(&s)) return 0;
    *out=s;return 1;
}
int wr_vpn_session_owner(const struct wr_vpn_session *s,char *out,size_t capacity)
{
    char text[64];size_t at;unsigned int i;int n;
    if (!valid_session(s) || !out) return 0;
    n=snprintf(text,sizeof(text),"wrvpn:%u:",s->id);if (n<0) return 0;at=(size_t)n;
    for (i=0;i<sizeof(s->nonce);i++) { snprintf(text+at,sizeof(text)-at,"%02x",s->nonce[i]);at+=2; }
    if (at+1>capacity) return 0;
    memcpy(out,text,at+1);return 1;
}
