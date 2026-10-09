#define _GNU_SOURCE
#include "writer-journal.h"
#include <assert.h>
static void put(const char *path,const char *value){FILE *fp=fopen(path,"w");assert(fp);assert(fputs(value,fp)>=0);assert(!fclose(fp));}
int main(void){
 char dir[]="/tmp/iot-writers-XXXXXX";const char *paths[]={"a","b","c","d","e","f","g","h"};
 struct wr_iot_service_transaction t;int token;size_t i;
 assert(mkdtemp(dir));assert(!chdir(dir));wr_iot_service_transaction_init(&t);
 assert(wr_iot_writer_journal_begin(14));assert(wr_iot_writer_journal_end(14));
 assert(!wr_iot_writer_journal_bind(&t));token=wr_iot_service_guard_enter(1);assert(token==1);
 t.lock.fd=wr_iot_service_guard_dup();assert(t.lock.fd>=0);
 for(i=0;i<8;i++){put(paths[i],"old\n");}
 assert(wr_iot_bundle_capture(&t.files,paths,8));t.active=1;
 assert(wr_iot_writer_journal_bind(&t));assert(!wr_iot_writer_journal_bind(&t));
 assert(!wr_iot_writer_journal_failed());{FILE *full=wr_iot_writer_fopen("/dev/full","w");assert(full);(void)fputs("partial",full);assert(wr_iot_writer_fclose(full)==EOF);assert(wr_iot_writer_journal_failed());}
 assert(!wr_iot_writer_fopen("missing-directory/file","w"));assert(wr_iot_writer_journal_failed());
 assert(wr_iot_writer_journal_begin(14));put("b","changed\n");assert(!wr_iot_writer_journal_unbind(&t));
 assert(!wr_iot_writer_journal_begin(6));assert(t.files.pending==14);assert(wr_iot_writer_journal_failed());
 assert(wr_iot_writer_journal_end(14));assert(wr_iot_bundle_restore(&t.files));
 assert(wr_iot_writer_journal_unbind(&t));assert(!wr_iot_writer_journal_failed());assert(wr_iot_service_transaction_finish(&t,"service.lock"));wr_iot_service_guard_leave(token);
 for(i=0;i<8;i++){assert(!unlink(paths[i]));}
 assert(!unlink("service.lock"));assert(!chdir("/tmp"));assert(!rmdir(dir));
 puts("PASS journal binding requires matching held guard; nested overlap refuses without clearing outer intents; confirmed writes recover; binding retains pending state; controller integration pending");return 0;
}
