#define _GNU_SOURCE
#include "service-lock.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
int main(void){
 char directory[]="/tmp/iot-service-lock-XXXXXX";struct wr_iot_service_lock first={-1},second={-1};int fd;
 assert(mkdtemp(directory));assert(!chdir(directory));
 assert(wr_iot_service_lock_take(&first,"service.lock"));assert(wr_iot_service_lock_valid(&first,"service.lock"));
 assert(!wr_iot_service_lock_take(&second,"service.lock")&&second.fd==-1);
 assert(!wr_iot_service_lock_take(&first,"service.lock"));
 assert(!unlink("service.lock"));fd=open("service.lock",O_CREAT|O_WRONLY,0600);assert(fd>=0);assert(!close(fd));
 assert(!wr_iot_service_lock_valid(&first,"service.lock"));wr_iot_service_lock_release(&first);assert(access("service.lock",F_OK)==0);
 assert(wr_iot_service_lock_take(&second,"service.lock"));wr_iot_service_lock_release(&second);wr_iot_service_lock_release(&second);
 assert(!symlink("service.lock","link"));assert(!wr_iot_service_lock_take(&first,"link"));
 assert(!chmod("service.lock",0644));assert(!wr_iot_service_lock_take(&first,"service.lock"));
 assert(!mkfifo("fifo",0600));assert(!wr_iot_service_lock_take(&first,"fifo"));
 assert(!unlink("link"));assert(!unlink("fifo"));assert(!unlink("service.lock"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS exclusive nonblocking service lock: contention, replacement detection, no unlink on release, private owner, symlink and FIFO rejection; service entry point integration pending");return 0;
}
