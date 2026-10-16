#define _GNU_SOURCE
#include "store.h"
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

#ifndef WR_VPN_STORE_WRITE
#define WR_VPN_STORE_WRITE write
#endif
#ifndef WR_VPN_STORE_FSYNC
#define WR_VPN_STORE_FSYNC fsync
#endif
#ifndef WR_VPN_STORE_RENAMEAT
#define WR_VPN_STORE_RENAMEAT renameat
#endif

static int wr_private(int fd, int directory)
{
    struct stat st;
    if (fstat(fd,&st) || st.st_uid!=geteuid()) return 0;
    if (directory) return S_ISDIR(st.st_mode) && (st.st_mode&0777)==0700;
    return S_ISREG(st.st_mode) && st.st_nlink==1 && (st.st_mode&0777)==0600;
}
int wr_vpn_store_open(const char *root)
{
    int fd;
    if (!root) return -1;
    fd=open(root,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (fd>=0 && !wr_private(fd,1)) { close(fd); return -1; }
    return fd;
}
static enum wr_vpn_store_result wr_lock(int root, int shared, int *fd)
{
    int lock, created=0;
    if (!wr_private(root,1)) return WR_VPN_STORE_INVALID;
    lock=openat(root,".lock",O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK,0600);
    if (lock>=0) created=1;
    else if (errno==EEXIST) lock=openat(root,".lock",O_RDWR|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (lock<0) return WR_VPN_STORE_IO;
    if (created && fchmod(lock,0600)) { close(lock); return WR_VPN_STORE_IO; }
    if (!wr_private(lock,0)) { close(lock); return WR_VPN_STORE_INVALID; }
    if (flock(lock,(shared?LOCK_SH:LOCK_EX)|LOCK_NB)) {
        int busy=errno==EWOULDBLOCK || errno==EAGAIN;
        close(lock); return busy?WR_VPN_STORE_BUSY:WR_VPN_STORE_IO;
    }
    *fd=lock; return WR_VPN_STORE_OK;
}
static void wr_be32(unsigned char *out, uint32_t n)
{ out[0]=(unsigned char)(n>>24); out[1]=(unsigned char)(n>>16); out[2]=(unsigned char)(n>>8); out[3]=(unsigned char)n; }
static uint32_t wr_u32(const unsigned char *p)
{ return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3]; }
static int wr_read_all(int fd, void *out, size_t n)
{
    unsigned char *p=out;
    while (n) {
        ssize_t got=read(fd,p,n);
        if (got<0 && errno==EINTR) continue;
        if (got<=0) return 0;
        p+=got; n-=(size_t)got;
    }
    return 1;
}
static int wr_write_all(int fd, const void *data, size_t n)
{
    const unsigned char *p=data;
    while (n) {
        ssize_t written=WR_VPN_STORE_WRITE(fd,p,n);
        if (written<0 && errno==EINTR) continue;
        if (written<=0) return 0;
        p+=written; n-=(size_t)written;
    }
    return 1;
}
static enum wr_vpn_store_result wr_read_record(int root, unsigned int id,
    struct wr_vpn_record *out, int *deleted)
{
    struct wr_vpn_record r;
    struct stat st;
    unsigned char header[32];
    char name[16]; int fd, valid;
    snprintf(name,sizeof(name),"%u",id);
    fd=openat(root,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd<0) return errno==ENOENT?WR_VPN_STORE_NOT_FOUND:WR_VPN_STORE_IO;
    memset(&r,0,sizeof(r));
    valid=wr_private(fd,0) && !fstat(fd,&st) && wr_read_all(fd,header,sizeof(header));
    if (valid) {
        r.id=wr_u32(header+8); r.protocol=(enum wr_vpn_protocol)wr_u32(header+12);
        r.revision=((uint64_t)wr_u32(header+16)<<32)|wr_u32(header+20);
        r.size=wr_u32(header+24);
        valid=!memcmp(header,"WRVP\1",5) && header[5]<=1 && !header[6] && !header[7] &&
            !wr_u32(header+28) && r.id==id && r.revision && r.size<=WR_VPN_CONFIG_MAX &&
            (r.protocol==WR_VPN_WIREGUARD || r.protocol==WR_VPN_AMNEZIAWG) &&
            st.st_size==(off_t)(sizeof(header)+r.size) &&
            (header[5]?r.size==0:r.size>0);
    }
    if (valid && r.size) valid=wr_read_all(fd,r.config,r.size) && !memchr(r.config,0,r.size);
    if (close(fd)) return WR_VPN_STORE_IO;
    if (!valid) return WR_VPN_STORE_INVALID;
    *deleted=header[5]; *out=r; return WR_VPN_STORE_OK;
}
enum wr_vpn_store_result wr_vpn_store_get(int root, unsigned int id,
                                        struct wr_vpn_record *out)
{
    enum wr_vpn_store_result result;
    struct wr_vpn_record record; int lock, deleted=0;
    if (!out || !id || id>WR_VPN_PROFILE_ID_MAX) return WR_VPN_STORE_INVALID;
    result=wr_lock(root,1,&lock); if (result!=WR_VPN_STORE_OK) return result;
    result=wr_read_record(root,id,&record,&deleted); close(lock);
    if (result==WR_VPN_STORE_OK && deleted) return WR_VPN_STORE_NOT_FOUND;
    if (result==WR_VPN_STORE_OK) *out=record;
    return result;
}
static enum wr_vpn_store_result wr_replace(int root, unsigned int id,
    enum wr_vpn_protocol protocol, const void *data, size_t size,
    uint64_t expected, uint64_t *revision, int deleting)
{
    enum wr_vpn_store_result result;
    struct wr_vpn_record old;
    unsigned char header[32];
    char target[16], temporary[64];
    int lock, fd=-1, deleted=0, ok, i;
    uint64_t next;
    if (!id || id>WR_VPN_PROFILE_ID_MAX || expected==UINT64_MAX ||
        (!deleting && ((protocol!=WR_VPN_WIREGUARD && protocol!=WR_VPN_AMNEZIAWG) ||
        !data || !size || size>WR_VPN_CONFIG_MAX || memchr(data,0,size))) ||
        (deleting && !expected)) return WR_VPN_STORE_INVALID;
    result=wr_lock(root,0,&lock); if (result!=WR_VPN_STORE_OK) return result;
    result=wr_read_record(root,id,&old,&deleted);
    if (!expected) {
        if (result==WR_VPN_STORE_OK) { result=WR_VPN_STORE_EXISTS; goto done; }
        if (result!=WR_VPN_STORE_NOT_FOUND) goto done;
    } else {
        if (result!=WR_VPN_STORE_OK) goto done;
        if (deleted) { result=WR_VPN_STORE_NOT_FOUND; goto done; }
        if (old.revision!=expected) { result=WR_VPN_STORE_STALE; goto done; }
    }
    next=expected+1;
    if (deleting) { protocol=old.protocol; size=0; }
    memset(header,0,sizeof(header)); memcpy(header,"WRVP\1",5); header[5]=(unsigned char)deleting;
    wr_be32(header+8,id); wr_be32(header+12,(uint32_t)protocol);
    wr_be32(header+16,(uint32_t)(next>>32)); wr_be32(header+20,(uint32_t)next);
    wr_be32(header+24,(uint32_t)size);
    for (i=0;i<32;i++) {
        snprintf(temporary,sizeof(temporary),".new-%ld-%d",(long)getpid(),i);
        fd=openat(root,temporary,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
        if (fd>=0 || errno!=EEXIST) break;
    }
    result=WR_VPN_STORE_IO;
    if (fd<0) goto done;
    ok=!fchmod(fd,0600) && wr_write_all(fd,header,sizeof(header)) && (!size || wr_write_all(fd,data,size)) && !WR_VPN_STORE_FSYNC(fd);
    if (close(fd)) ok=0;
    snprintf(target,sizeof(target),"%u",id);
    if (!ok || WR_VPN_STORE_RENAMEAT(root,temporary,root,target)) {
        unlinkat(root,temporary,0); goto done;
    }
    if (revision) *revision=next;
    result=WR_VPN_STORE_FSYNC(root)?WR_VPN_STORE_COMMITTED_UNSYNCED:WR_VPN_STORE_OK;
done:
    close(lock); return result;
}
enum wr_vpn_store_result wr_vpn_store_put(int root, unsigned int id,
    enum wr_vpn_protocol protocol, const void *config, size_t size,
    uint64_t expected, uint64_t *revision)
{ return wr_replace(root,id,protocol,config,size,expected,revision,0); }
enum wr_vpn_store_result wr_vpn_store_delete(int root, unsigned int id,
    uint64_t expected, uint64_t *revision)
{ return wr_replace(root,id,WR_VPN_WIREGUARD,NULL,0,expected,revision,1); }
