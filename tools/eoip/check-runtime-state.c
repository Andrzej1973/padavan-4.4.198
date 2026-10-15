#include <assert.h>
#include "runtime-state.h"
int main(void)
{
 char directory[]="/tmp/wr-eoip-state-XXXXXX",path[PATH_MAX];unsigned index;FILE *fp;
 struct wr_eoip_state first={.fd=-1},second={.fd=-1};
 assert(mkdtemp(directory));assert(wr_eoip_state_lock(directory,&first));
 assert(!wr_eoip_state_lock(directory,&second));
 assert(fcntl(first.fd,F_GETFD)&FD_CLOEXEC);
 assert(wr_eoip_state_read(&first,0,&index)==1&&index==0);
 assert(wr_eoip_state_write(&first,0,10));assert(wr_eoip_state_read(&first,0,&index)==2&&index==10);
 assert(wr_eoip_state_write(&first,0,10));assert(!wr_eoip_state_write(&first,0,11));
 assert(!wr_eoip_state_clear(&first,0,11));assert(wr_eoip_state_clear(&first,0,10));
 assert(wr_eoip_state_clear(&first,0,10));assert(!wr_eoip_state_write(&first,8,10));
 snprintf(path,sizeof(path),"%s/0",directory);fp=fopen(path,"w");assert(fp);fputs("v1 0010\n",fp);fclose(fp);assert(chmod(path,0600)==0);
 assert(wr_eoip_state_read(&first,0,&index)==0&&index==0);assert(!wr_eoip_state_write(&first,0,10));
 assert(unlink(path)==0&&symlink("/etc/passwd",path)==0);
 assert(wr_eoip_state_read(&first,0,&index)==0);assert(!wr_eoip_state_clear(&first,0,10));assert(unlink(path)==0);
 wr_eoip_state_unlock(&first);assert(wr_eoip_state_lock(directory,&second));wr_eoip_state_unlock(&second);
 assert(chmod(directory,0777)==0);assert(!wr_eoip_state_lock(directory,&first));assert(chmod(directory,0700)==0);
 snprintf(path,sizeof(path),"%s/lock",directory);unlink(path);assert(rmdir(directory)==0);
 puts("PASS EoIP runtime state: exclusive lock, atomic identity, mismatch/corrupt/symlink refusal, private directory");return 0;
}
