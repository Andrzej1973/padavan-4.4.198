#define _GNU_SOURCE
#include "saved-file.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 char directory[]="/tmp/iot-saved-file-XXXXXX";struct wr_iot_saved_file saved,before;FILE *fp;int fd;
 assert(mkdtemp(directory));assert(!chdir(directory));memset(&saved,0,sizeof(saved));
 fp=fopen("config","w");assert(fp);assert(fputs("previous-config\n",fp)>=0);assert(!fclose(fp));
 assert(wr_iot_saved_capture(&saved,"config"));assert(saved.existed&&saved.size==16&&!memcmp(saved.data,"previous-config\n",16));
 before=saved;assert(!wr_iot_saved_capture(&saved,"config"));assert(!memcmp(&saved,&before,sizeof(saved)));wr_iot_saved_release(&saved);
 assert(wr_iot_saved_capture(&saved,"missing")&&!saved.existed&&!saved.data);
 assert(!symlink("config","link"));before=saved;assert(!wr_iot_saved_capture(&saved,"link"));assert(!memcmp(&saved,&before,sizeof(saved)));
 assert(!wr_iot_saved_capture(&saved,"."));assert(!mkfifo("fifo",0600));assert(!wr_iot_saved_capture(&saved,"fifo"));
 fd=open("large",O_WRONLY|O_CREAT,0600);assert(fd>=0);assert(!ftruncate(fd,WR_IOT_SAVED_LIMIT+1));assert(!close(fd));assert(!wr_iot_saved_capture(&saved,"large"));
 assert(!unlink("config"));assert(!unlink("link"));assert(!unlink("fifo"));assert(!unlink("large"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS bounded previous-file capture: contents, metadata, absent file, no overwrite of existing snapshot, symlink/nonregular/oversize rejection. Restore and service integration pending.");return 0;
}
