#define _GNU_SOURCE
#include "restore-file.h"
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
  assert(wr_iot_saved_restore(&saved,&generated,"config"));
  fp=fopen("config","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,"previous-config\n"));assert(!fclose(fp));
  assert(!stat("config",&restored));assert((restored.st_mode&0777)==(saved.metadata.st_mode&0777));
  assert(wr_iot_generated_capture(&generated,"config"));
  fp=fopen("replacement","w");assert(fp);assert(fputs("foreign\n",fp)>=0);assert(!fclose(fp));assert(!rename("replacement","config"));
  assert(!wr_iot_saved_restore(&saved,&generated,"config"));
 }
wr_iot_saved_release(&saved);
 assert(wr_iot_saved_capture(&saved,"missing")&&!saved.existed&&!saved.data);
 assert(!symlink("config","link"));before=saved;assert(!wr_iot_saved_capture(&saved,"link"));assert(!memcmp(&saved,&before,sizeof(saved)));
 assert(!wr_iot_saved_capture(&saved,"."));assert(!mkfifo("fifo",0600));assert(!wr_iot_saved_capture(&saved,"fifo"));
 fd=open("large",O_WRONLY|O_CREAT,0600);assert(fd>=0);assert(!ftruncate(fd,WR_IOT_SAVED_LIMIT+1));assert(!close(fd));assert(!wr_iot_saved_capture(&saved,"large"));
 assert(!unlink("config"));assert(!unlink("link"));assert(!unlink("fifo"));assert(!unlink("large"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS bounded previous-file capture: contents, metadata, absent file, no overwrite of existing snapshot, symlink/nonregular/oversize rejection. Atomic contents/mode restore and foreign inode rejection passed; service integration pending.");return 0;
}
