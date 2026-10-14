#include "doh-instance-status.h"
#include <assert.h>
#include <stdlib.h>
static void put(const char *path,const char *text){FILE *f=fopen(path,"w");assert(f);assert(fputs(text,f)>=0);assert(!fclose(f));}
int main(void)
{
 char work[]="/tmp/wr-doh-observer-XXXXXX";struct wr_doh_instances state;
 assert(mkdtemp(work));assert(!chdir(work));assert(!mkdir("pids",0700));assert(!mkdir("proc",0700));
 assert(!mkdir("proc/123",0700));assert(!symlink("/usr/sbin/https_dns_proxy","proc/123/exe"));
 state=wr_doh_observe(3,"pids","proc");assert(state.configured==3&&!state.owned&&!state.unknown);
 put("pids/0.pid","123\n");state=wr_doh_observe(3,"pids","proc");assert(state.owned==1&&!state.unknown);
 put("pids/1.pid","123\n");state=wr_doh_observe(3,"pids","proc");assert(state.owned==1&&state.duplicate==2&&state.unknown==2);
 put("pids/1.pid","124\n");assert(!mkdir("proc/124",0700));assert(!symlink("/usr/sbin/https_dns_proxy","proc/124/exe"));
 state=wr_doh_observe(3,"pids","proc");assert(state.owned==3&&!state.unknown);
 state=wr_doh_observe(1,"pids","proc");assert(state.configured==1&&state.owned==3);
 assert(!unlink("proc/124/exe"));assert(!symlink("/usr/sbin/other","proc/124/exe"));
 state=wr_doh_observe(3,"pids","proc");assert(state.owned==1&&!state.unknown);
 {const char *bad[]={"", "1\n", "-2\n", "123 garbage\n", "9999999999999999", "4294967296", "123\n\n"};size_t i;
  for(i=0;i<sizeof(bad)/sizeof(bad[0]);i++){put("pids/1.pid",bad[i]);state=wr_doh_observe(3,"pids","proc");assert(state.owned==1&&state.unknown==2);}}
 {FILE *f=fopen("pids/1.pid","wb");assert(f);assert(fwrite("123\0hidden",1,10,f)==10);assert(!fclose(f));state=wr_doh_observe(3,"pids","proc");assert(state.unknown==2);}
 state=wr_doh_observe(3,"pids","missing-proc");assert(state.unknown==15&&!state.owned);
 assert(!unlink("pids/1.pid"));assert(!symlink("0.pid","pids/1.pid"));state=wr_doh_observe(3,"pids","proc");assert(state.unknown==2);
 assert(!unlink("pids/0.pid"));assert(!unlink("pids/1.pid"));assert(!rmdir("pids"));
 assert(!unlink("proc/123/exe"));assert(!unlink("proc/124/exe"));assert(!rmdir("proc/123"));assert(!rmdir("proc/124"));assert(!rmdir("proc"));
 assert(!chdir("/tmp"));assert(!rmdir(work));puts("PASS DoH slot ownership, duplicate PID, missing/wrong executable and malformed/symlink PID files; no DNS health inference");return 0;
}
