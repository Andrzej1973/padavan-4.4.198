#define _GNU_SOURCE
#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#include "store.h"

static int fail_write, fail_sync, sync_calls, fail_rename, short_write;
static ssize_t fixture_write(int fd,const void *data,size_t size)
{
    if (fail_write) { errno=ENOSPC; return -1; }
    return write(fd,data,short_write && size>3?3:size);
}
static int fixture_sync(int fd)
{
    if (++sync_calls==fail_sync) { errno=EIO; return -1; }
    return fsync(fd);
}
static int fixture_rename(int oldroot,const char *old,int newroot,const char *newname)
{
    if (fail_rename) { errno=EIO; return -1; }
    return renameat(oldroot,old,newroot,newname);
}
#define WR_VPN_STORE_WRITE fixture_write
#define WR_VPN_STORE_FSYNC fixture_sync
#define WR_VPN_STORE_RENAMEAT fixture_rename
#include "store.c"

static void no_temporary_files(int root)
{
    DIR *dir=fdopendir(openat(root,".",O_RDONLY|O_DIRECTORY));
    struct dirent *entry;
    assert(dir);
    while ((entry=readdir(dir))) assert(strncmp(entry->d_name,".new-",5));
    closedir(dir);
}
static void expect_config(int root,unsigned int id,const char *value,uint64_t revision)
{
    struct wr_vpn_record r;
    assert(wr_vpn_store_get(root,id,&r)==WR_VPN_STORE_OK);
    assert(r.id==id && r.revision==revision && r.size==strlen(value));
    assert(!memcmp(r.config,value,r.size));
}
int main(void)
{
    char path[]="/tmp/wrvpn-store-XXXXXX",alias[256];
    const char *first="[Interface]\nPrivateKey = synthetic-AWG-only\n";
    const char *second="[Interface]\nPrivateKey = synthetic-WG-only\n";
    struct wr_vpn_record out,previous;
    uint64_t revision=999;
    int root,held,fd; struct stat st; mode_t previous_umask;
    assert(mkdtemp(path)); root=wr_vpn_store_open(path); assert(root>=0);
    memset(&out,0xa5,sizeof(out)); previous=out;
    previous_umask=umask(0777);
    assert(wr_vpn_store_get(root,1,&out)==WR_VPN_STORE_NOT_FOUND);
    assert(!memcmp(&out,&previous,sizeof(out)));
    assert(wr_vpn_store_put(root,1,WR_VPN_AMNEZIAWG,first,strlen(first),0,&revision)==WR_VPN_STORE_OK && revision==1);
    umask(previous_umask);
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,second,strlen(second),0,&revision)==WR_VPN_STORE_OK);
    expect_config(root,1,first,1); expect_config(root,2,second,1);
    assert(!fstatat(root,"1",&st,AT_SYMLINK_NOFOLLOW) && (st.st_mode&0777)==0600);
    assert(wr_vpn_store_put(root,1,WR_VPN_WIREGUARD,second,strlen(second),0,NULL)==WR_VPN_STORE_EXISTS);
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,first,strlen(first),99,NULL)==WR_VPN_STORE_STALE);
    assert(wr_vpn_store_delete(root,2,99,NULL)==WR_VPN_STORE_STALE);
    held=openat(root,".lock",O_RDWR); assert(held>=0 && !flock(held,LOCK_EX|LOCK_NB));
    assert(wr_vpn_store_get(root,1,&out)==WR_VPN_STORE_BUSY);
    assert(wr_vpn_store_delete(root,1,1,NULL)==WR_VPN_STORE_BUSY);
    assert(wr_vpn_store_put(root,3,WR_VPN_WIREGUARD,second,strlen(second),0,NULL)==WR_VPN_STORE_BUSY);
    close(held);
    /* Pre-commit failures must preserve both the old and unrelated profiles. */
    fail_write=1;
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,first,strlen(first),1,NULL)==WR_VPN_STORE_IO);
    fail_write=0; sync_calls=0; fail_sync=1;
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,first,strlen(first),1,NULL)==WR_VPN_STORE_IO);
    fail_sync=0; fail_rename=1;
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,first,strlen(first),1,NULL)==WR_VPN_STORE_IO);
    fail_rename=0;
    expect_config(root,1,first,1); expect_config(root,2,second,1); no_temporary_files(root);
    short_write=1; sync_calls=0; fail_sync=2; revision=999;
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,first,strlen(first),1,&revision)==WR_VPN_STORE_COMMITTED_UNSYNCED && revision==2);
    short_write=0; fail_sync=0;
    expect_config(root,2,first,2);
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,second,strlen(second),1,NULL)==WR_VPN_STORE_STALE);
    assert(wr_vpn_store_put(root,2,WR_VPN_WIREGUARD,second,strlen(second),2,&revision)==WR_VPN_STORE_OK && revision==3);
    assert(wr_vpn_store_delete(root,1,1,&revision)==WR_VPN_STORE_OK && revision==2);
    assert(wr_vpn_store_get(root,1,&out)==WR_VPN_STORE_NOT_FOUND);
    assert(wr_vpn_store_put(root,1,WR_VPN_WIREGUARD,second,strlen(second),0,NULL)==WR_VPN_STORE_EXISTS);
    expect_config(root,2,second,3);
    /* Restore / malformed paths may not follow links or replace foreign data. */
    assert(!symlinkat("2",root,"3"));
    assert(wr_vpn_store_put(root,3,WR_VPN_WIREGUARD,first,strlen(first),0,NULL)==WR_VPN_STORE_IO);
    assert(!unlinkat(root,"3",0));
    assert(!linkat(root,"2",root,"3",0));
    assert(wr_vpn_store_get(root,2,&out)==WR_VPN_STORE_INVALID);
    assert(!unlinkat(root,"3",0)); expect_config(root,2,second,3);
    fd=openat(root,"4",O_WRONLY|O_CREAT|O_EXCL,0600); assert(fd>=0);
    assert(write(fd,"bad",3)==3); close(fd);
    memset(&out,0xa5,sizeof(out)); previous=out;
    assert(wr_vpn_store_get(root,4,&out)==WR_VPN_STORE_INVALID && !memcmp(&out,&previous,sizeof(out)));
    assert(wr_vpn_store_put(root,4,WR_VPN_WIREGUARD,first,strlen(first),0,NULL)==WR_VPN_STORE_INVALID);
    assert(wr_vpn_store_put(root,5,WR_VPN_WIREGUARD,"x\0y",3,0,NULL)==WR_VPN_STORE_INVALID);
    assert(wr_vpn_store_put(root,5,WR_VPN_WIREGUARD,first,WR_VPN_CONFIG_MAX+1u,0,NULL)==WR_VPN_STORE_INVALID);
    assert(wr_vpn_store_delete(root,2,0,NULL)==WR_VPN_STORE_INVALID);
    snprintf(alias,sizeof(alias),"%s/alias",path); assert(!symlink(path,alias));
    assert(wr_vpn_store_open(alias)<0); assert(!unlink(alias));
    assert(!chmod(path,0755)); assert(wr_vpn_store_open(path)<0);
    assert(wr_vpn_store_get(root,2,&out)==WR_VPN_STORE_INVALID); assert(!chmod(path,0700));
    no_temporary_files(root);
    { DIR *dir=fdopendir(openat(root,".",O_RDONLY|O_DIRECTORY)); struct dirent *entry;
      assert(dir); while ((entry=readdir(dir))) if (strcmp(entry->d_name,".") && strcmp(entry->d_name,"..")) assert(!unlinkat(root,entry->d_name,0));
      closedir(dir); }
    close(root); assert(!rmdir(path));
    puts("PASS VPN profile file store: isolated records, revision conflicts, locks, atomic failure handling, tombstones, unsafe path refusal; no tunnel/flash integration");
    return 0;
}
