#define _GNU_SOURCE
#include "saved-bundle.h"
#include <assert.h>
static void write_file(const char *path,const char *text){FILE *fp=fopen(path,"w");assert(fp);assert(fputs(text,fp)>=0);assert(!fclose(fp));}
static void expect(const char *path,const char *text){char buf[64];FILE *fp=fopen(path,"r");assert(fp);assert(fgets(buf,sizeof(buf),fp));assert(!strcmp(buf,text));assert(!fclose(fp));}
int main(void){char dir[]="/tmp/iot-write-journal-XXXXXX";const char *paths[]={"main","helper"};struct wr_iot_saved_bundle bundle;
 assert(mkdtemp(dir));assert(!chdir(dir));write_file("main","previous\n");memset(&bundle,0,sizeof(bundle));assert(wr_iot_bundle_capture(&bundle,paths,2));
 assert(wr_iot_bundle_write_begin(&bundle,0));write_file("main","candidate\n");assert(wr_iot_bundle_write_end(&bundle,0));
 assert(wr_iot_bundle_write_begin(&bundle,1));write_file("helper","partial\n");
 assert(!wr_iot_bundle_seal(&bundle));assert(!wr_iot_bundle_restore(&bundle));expect("main","previous\n");expect("helper","partial\n");assert(bundle.pending==2&&bundle.restored==1&&bundle.saved[0].data);
 assert(!wr_iot_bundle_write_begin(&bundle,0));assert(wr_iot_bundle_write_end(&bundle,1));assert(wr_iot_bundle_restore(&bundle));assert(bundle.sealed);assert(access("helper",F_OK)!=0);expect("main","previous\n");wr_iot_bundle_release(&bundle);
 memset(&bundle,0,sizeof(bundle));assert(wr_iot_bundle_capture(&bundle,paths,2));assert(wr_iot_bundle_write_begin(&bundle,0));write_file("main","second\n");assert(wr_iot_bundle_write_end(&bundle,0));assert(wr_iot_bundle_seal(&bundle));assert(wr_iot_bundle_restore(&bundle));expect("main","previous\n");wr_iot_bundle_release(&bundle);
 assert(!unlink("main"));assert(!chdir("/tmp"));assert(!rmdir(dir));puts("PASS owned write journal: incomplete write blocks completion, confirmed file recovers before final seal, snapshots retained, end+retry recovers prior absence; RC writer instrumentation pending");return 0;}
