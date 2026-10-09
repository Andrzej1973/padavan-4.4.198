#define _GNU_SOURCE
#include "uts-state.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
int main(void){
 struct wr_iot_uts_state saved,current;char namespace[128];const char *parent=getenv("WR_IOT_PARENT_UTSNS");ssize_t n;
 n=readlink("/proc/self/ns/uts",namespace,sizeof(namespace)-1);if(geteuid()!=0||!parent||n<0)return 2;
 namespace[n]=0;if(!strcmp(namespace,parent))return 2;
 assert(wr_iot_uts_capture(&saved));assert(!sethostname("iot-test",8));assert(!setdomainname("iot-fixture.invalid",19));
 assert(wr_iot_uts_capture(&current));assert(!strcmp(current.hostname,"iot-test"));assert(!strcmp(current.domain,"iot-fixture.invalid"));
 assert(wr_iot_uts_restore(&saved));assert(wr_iot_uts_capture(&current));assert(!strcmp(current.hostname,saved.hostname));assert(!strcmp(current.domain,saved.domain));
 memset(&current,'x',sizeof(current));assert(!wr_iot_uts_restore(&current));
 puts("PASS read-only UTS snapshot and actual hostname/domain restore in private UTS namespace; concurrent writer/partial-error and RC integration pending");return 0;
}
