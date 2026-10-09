#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <dirent.h>
static int restore_fault;
static int failing_mkstemp(char *path){if(restore_fault==1){errno=ENOSPC;return -1;}return mkstemp(path);}
static ssize_t failing_write(int fd,const void *data,size_t size){if(restore_fault==2){errno=EIO;return -1;}return write(fd,data,size);}
static int failing_fsync(int fd){if(restore_fault==3){errno=EIO;return -1;}return fsync(fd);}
static int failing_close(int fd){int result=close(fd);return restore_fault==4?-1:result;}
static int failing_rename(const char *from,const char *to){if(restore_fault==5){errno=EACCES;return -1;}return rename(from,to);}
#define WR_IOT_RESTORE_MKSTEMP failing_mkstemp
#define WR_IOT_RESTORE_WRITE failing_write
#define WR_IOT_RESTORE_FSYNC failing_fsync
#define WR_IOT_RESTORE_CLOSE failing_close
#define WR_IOT_RESTORE_RENAME failing_rename
#include "saved-bundle.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 char directory[]="/tmp/iot-saved-file-XXXXXX";struct wr_iot_saved_file saved,before;FILE *fp;int fd;
 assert(mkdtemp(directory));assert(!chdir(directory));memset(&saved,0,sizeof(saved));
 fp=fopen("config","w");assert(fp);assert(fputs("previous-config\n",fp)>=0);assert(!fclose(fp));
 assert(wr_iot_saved_capture(&saved,"config"));assert(saved.existed&&saved.size==16&&!memcmp(saved.data,"previous-config\n",16));
 before=saved;assert(!wr_iot_saved_capture(&saved,"config"));assert(!memcmp(&saved,&before,sizeof(saved)));{
  struct wr_iot_generated_file generated;struct stat restored;char text[32];
  fp=fopen("config","w");assert(fp);assert(fputs("new\n",fp)>=0);assert(!fclose(fp));assert(!chmod("config",0600));
  assert(wr_iot_generated_capture(&generated,"config"));
  {
   int mode;
   for(mode=1;mode<=5;mode++) {
    DIR *dir;struct dirent *entry;
    restore_fault=mode;
    assert(!wr_iot_saved_restore(&saved,&generated,"config"));
    restore_fault=0;
    fp=fopen("config","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"new\n"));assert(!fclose(fp));
    assert(saved.size==16&&!memcmp(saved.data,"previous-config\n",16));
    dir=opendir(".");assert(dir);while((entry=readdir(dir)))assert(!strstr(entry->d_name,".iot-restore."));closedir(dir);
   }
  }
  assert(wr_iot_saved_restore(&saved,&generated,"config"));
  fp=fopen("config","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"previous-config\n"));assert(!fclose(fp));
  assert(!stat("config",&restored));assert((restored.st_mode&0777)==(saved.metadata.st_mode&0777));
  assert(wr_iot_generated_capture(&generated,"config"));
  fp=fopen("replacement","w");assert(fp);assert(fputs("foreign\n",fp)>=0);assert(!fclose(fp));assert(!rename("replacement","config"));
  assert(!wr_iot_saved_restore(&saved,&generated,"config"));
 }
wr_iot_saved_release(&saved);
 assert(wr_iot_saved_capture(&saved,"missing")&&!saved.existed&&!saved.data);
 {struct wr_iot_generated_file generated;
  fp=fopen("missing","w");assert(fp);assert(fputs("created\n",fp)>=0);assert(!fclose(fp));
  assert(wr_iot_generated_capture(&generated,"missing"));assert(wr_iot_saved_restore(&saved,&generated,"missing"));assert(access("missing",F_OK)!=0);
 }

 assert(!symlink("config","link"));before=saved;assert(!wr_iot_saved_capture(&saved,"link"));assert(!memcmp(&saved,&before,sizeof(saved)));
 assert(!wr_iot_saved_capture(&saved,"."));assert(!mkfifo("fifo",0600));assert(!wr_iot_saved_capture(&saved,"fifo"));
 fd=open("large",O_WRONLY|O_CREAT,0600);assert(fd>=0);assert(!ftruncate(fd,WR_IOT_SAVED_LIMIT+1));assert(!close(fd));assert(!wr_iot_saved_capture(&saved,"large"));
 {
  struct wr_iot_saved_bundle bundle;const char *paths[]={"config","absent-helper"};char text[32];
  memset(&bundle,0,sizeof(bundle));assert(wr_iot_bundle_capture(&bundle,paths,2));
  assert(!wr_iot_bundle_restore(&bundle));
  fp=fopen("config","w");assert(fp);assert(fputs("generated\n",fp)>=0);assert(!fclose(fp));
  fp=fopen("absent-helper","w");assert(fp);assert(fputs("helper\n",fp)>=0);assert(!fclose(fp));
  assert(wr_iot_bundle_seal(&bundle));assert(!wr_iot_bundle_seal(&bundle));
  restore_fault=5;assert(!wr_iot_bundle_restore(&bundle));assert(bundle.saved[0].data);restore_fault=0;
  assert(wr_iot_bundle_restore(&bundle));assert(wr_iot_bundle_restore(&bundle));
  fp=fopen("config","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"foreign\n"));assert(!fclose(fp));
  assert(access("absent-helper",F_OK)!=0);wr_iot_bundle_release(&bundle);assert(!bundle.count);
  {const char *duplicates[]={"config","config"};assert(!wr_iot_bundle_capture(&bundle,duplicates,2));assert(!bundle.count);}
  {const char *invalid[]={"config","fifo"};assert(!wr_iot_bundle_capture(&bundle,invalid,2));assert(!bundle.count);}
 }
 assert(!unlink("config"));assert(!unlink("link"));assert(!unlink("fifo"));assert(!unlink("large"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS bounded previous-file capture: contents, metadata, absent file, no overwrite of existing snapshot, symlink/nonregular/oversize rejection. Atomic contents/mode restore and foreign inode rejection passed; restore failure cleanup and prior absence verified; bundle capture/partial restore retry verified; service integration pending.");return 0;
}
