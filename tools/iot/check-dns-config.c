#define _GNU_SOURCE
#include "dns-config.h"
#include <assert.h>
static void put(const char *path,const char *value){FILE *fp=fopen(path,"w");assert(fp);assert(fputs(value,fp)>=0);assert(!fclose(fp));}
int main(void){char dir[]="/tmp/iot-dns-config-XXXXXX";unsigned int port=999;
 assert(mkdtemp(dir));assert(!chdir(dir));put("main","cache-size=100\n");assert(wr_iot_dns_config_port("main",&port)&&port==53);
 put("main","port=1053\nconf-file=extra\n");put("extra"," port = 0 # disabled\n");assert(wr_iot_dns_config_port("main",&port)&&port==0);
 put("extra","port=65536\n");port=999;assert(!wr_iot_dns_config_port("main",&port)&&port==999);
 put("extra","conf-file=main\n");assert(!wr_iot_dns_config_port("main",&port));
 put("main","conf-dir=additional\n");assert(!wr_iot_dns_config_port("main",&port));
 assert(!symlink("extra","link"));assert(!wr_iot_dns_config_port("link",&port));assert(!unlink("link"));
 assert(!unlink("main"));assert(!unlink("extra"));assert(!chdir("/tmp"));assert(!rmdir(dir));
 puts("PASS bounded effective DNS port reader: default, nested override, disabled DNS, invalid port, include cycle and symlink rejection; controller integration pending");return 0;
}
