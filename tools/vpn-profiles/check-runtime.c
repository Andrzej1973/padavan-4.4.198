#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include "runtime-state.h"

int main(void)
{
    char path[]="/tmp/wrvpn-runtime-XXXXXX",owner[64],other[64],record[256];
    struct wr_vpn_runtime runtime={-1,-1},competing={-1,-1};
    struct wr_vpn_session intent,active,second,out,before;
    int fd;struct stat st;
    assert(mkdtemp(path));
    assert(wr_vpn_runtime_lock(path,&runtime)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_runtime_lock(path,&competing)==WR_VPN_RUNTIME_BUSY);
    assert(competing.root==-1 && competing.lock==-1);
    assert((fcntl(runtime.root,F_GETFD)&FD_CLOEXEC) && (fcntl(runtime.lock,F_GETFD)&FD_CLOEXEC));
    assert(wr_vpn_session_new(&intent,1,WR_VPN_AMNEZIAWG,UINT64_C(0x100000001)));
    assert(wr_vpn_session_new(&second,2,WR_VPN_WIREGUARD,3));
    assert(wr_vpn_session_owner(&intent,owner,sizeof(owner)));
    assert(wr_vpn_session_owner(&second,other,sizeof(other)) && strcmp(owner,other));
    memset(&out,0xa5,sizeof(out));before=out;
    assert(wr_vpn_runtime_read(&runtime,1,&out)==WR_VPN_RUNTIME_ABSENT && !memcmp(&out,&before,sizeof(out)));
    assert(wr_vpn_runtime_put(&runtime,&intent,NULL)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_runtime_put(&runtime,&second,NULL)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_runtime_put(&runtime,&intent,NULL)==WR_VPN_RUNTIME_STALE);
    assert(wr_vpn_runtime_read(&runtime,1,&out)==WR_VPN_RUNTIME_OK && out.revision==intent.revision && !out.index);
    active=intent;active.index=41;
    assert(wr_vpn_runtime_put(&runtime,&active,&intent)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_session_owner(&active,other,sizeof(other)) && !strcmp(owner,other));
    assert(wr_vpn_runtime_put(&runtime,&active,&intent)==WR_VPN_RUNTIME_STALE);
    assert(wr_vpn_runtime_put(&runtime,&active,&active)==WR_VPN_RUNTIME_INVALID);
    assert(wr_vpn_runtime_clear(&runtime,&intent)==WR_VPN_RUNTIME_STALE);
    out=active;out.nonce[0]^=1;
    assert(wr_vpn_runtime_clear(&runtime,&out)==WR_VPN_RUNTIME_STALE);
    assert(wr_vpn_runtime_clear(&runtime,&active)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_runtime_read(&runtime,2,&out)==WR_VPN_RUNTIME_OK && out.id==2 && !memcmp(out.nonce,second.nonce,16));
    assert(wr_vpn_runtime_clear(&runtime,&second)==WR_VPN_RUNTIME_OK);
    assert(wr_vpn_runtime_put(&runtime,&active,NULL)==WR_VPN_RUNTIME_INVALID);
    fd=openat(runtime.root,"1",O_WRONLY|O_CREAT|O_EXCL,0600);assert(fd>=0);assert(write(fd,"bad",3)==3);close(fd);
    assert(wr_vpn_runtime_read(&runtime,1,&out)==WR_VPN_RUNTIME_INVALID);
    assert(wr_vpn_runtime_put(&runtime,&intent,NULL)==WR_VPN_RUNTIME_INVALID);
    assert(wr_vpn_runtime_clear(&runtime,&intent)==WR_VPN_RUNTIME_INVALID);
    assert(!unlinkat(runtime.root,"1",0));
    assert(!symlinkat("2",runtime.root,"1"));
    assert(wr_vpn_runtime_read(&runtime,1,&out)!=WR_VPN_RUNTIME_ABSENT);
    assert(wr_vpn_runtime_put(&runtime,&intent,NULL)!=WR_VPN_RUNTIME_OK);
    assert(!unlinkat(runtime.root,"1",0));
    assert(wr_vpn_runtime_put(&runtime,&intent,NULL)==WR_VPN_RUNTIME_OK);
    assert(!linkat(runtime.root,"1",runtime.root,"alias",0));
    assert(wr_vpn_runtime_read(&runtime,1,&out)==WR_VPN_RUNTIME_INVALID);
    assert(!unlinkat(runtime.root,"alias",0));
    assert(!fstatat(runtime.root,"1",&st,AT_SYMLINK_NOFOLLOW) && (st.st_mode&0777)==0600);
    fd=openat(runtime.root,"1",O_WRONLY);assert(fd>=0);assert(!fchmod(fd,0644));close(fd);
    assert(wr_vpn_runtime_read(&runtime,1,&out)==WR_VPN_RUNTIME_INVALID);
    fd=openat(runtime.root,"1",O_WRONLY);assert(fd>=0);assert(!fchmod(fd,0600));close(fd);
    assert(wr_vpn_runtime_clear(&runtime,&intent)==WR_VPN_RUNTIME_OK);
    {
        struct wr_vpn_record applied,loaded;
        memset(&applied,0,sizeof(applied));memset(&loaded,0,sizeof(loaded));
        applied.id=1;applied.protocol=WR_VPN_WIREGUARD;applied.revision=9;applied.size=32;
        memset(applied.config,'k',applied.size);
        assert(wr_vpn_runtime_snapshot_get(&runtime,1,&loaded)==WR_VPN_RUNTIME_ABSENT);
        assert(wr_vpn_runtime_snapshot_put(&runtime,&applied)==WR_VPN_RUNTIME_OK);
        assert(wr_vpn_runtime_snapshot_get(&runtime,1,&loaded)==WR_VPN_RUNTIME_OK);
        assert(loaded.id==1 && loaded.protocol==WR_VPN_WIREGUARD && loaded.revision==9);
        assert(loaded.size==applied.size && !memcmp(loaded.config,applied.config,applied.size));
        assert(!fstatat(runtime.root,"snapshot-1",&st,AT_SYMLINK_NOFOLLOW) &&
               (st.st_mode&0777)==0600 && st.st_nlink==1);
        applied.size=0;assert(wr_vpn_runtime_snapshot_put(&runtime,&applied)==WR_VPN_RUNTIME_INVALID);
        fd=openat(runtime.root,"snapshot-1",O_WRONLY|O_TRUNC);
        assert(fd>=0);assert(write(fd,"WRVG\1bad",8)==8);close(fd);
        assert(wr_vpn_runtime_snapshot_get(&runtime,1,&loaded)==WR_VPN_RUNTIME_INVALID);
        assert(!unlinkat(runtime.root,"snapshot-1",0));
        assert(!symlinkat("2",runtime.root,"snapshot-1"));
        assert(wr_vpn_runtime_snapshot_get(&runtime,1,&loaded)!=WR_VPN_RUNTIME_ABSENT);
        assert(wr_vpn_runtime_snapshot_put(&runtime,&applied)==WR_VPN_RUNTIME_INVALID);
        assert(!unlinkat(runtime.root,"snapshot-1",0));
    }
    wr_vpn_runtime_unlock(&runtime);
    assert(wr_vpn_runtime_lock(path,&runtime)==WR_VPN_RUNTIME_OK);
    wr_vpn_runtime_unlock(&runtime);
    snprintf(record,sizeof(record),"%s/.operation-lock",path);assert(!unlink(record));assert(!rmdir(path));
    puts("PASS VPN private runtime sessions: operation lock, independent profiles, random owner, intent/index transition, stale/corrupt/path rejection, applied snapshot round trip; no network actions");
    return 0;
}
