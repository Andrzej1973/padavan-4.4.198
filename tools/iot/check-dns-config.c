#define _GNU_SOURCE
/* Reproduce pinned shutils.h:141 include order used by services_ex.c. */
#define isblank(c) ((c) == ' ' || (c) == '\t')
#include "dns-config.h"
#include <assert.h>
static void put(const char *path,const char *value){FILE *fp=fopen(path,"w");assert(fp);assert(fputs(value,fp)>=0);assert(!fclose(fp));}
int main(void){char dir[]="/tmp/iot-dns-config-XXXXXX";unsigned int port=999;
 assert(mkdtemp(dir));assert(!chdir(dir));put("main","cache-size=100\n");assert(wr_iot_dns_config_port("main",&port)&&port==53);
 put("main","port=1053\nconf-file=extra\n");put("extra"," port = 0 # disabled\n");assert(wr_iot_dns_config_port("main",&port)&&port==0);
 put("extra","port=65536\n");port=999;assert(!wr_iot_dns_config_port("main",&port)&&port==999);
 put("extra","conf-file=main\n");assert(!wr_iot_dns_config_port("main",&port));
 put("main","conf-script=/bin/echo port=1053\n");assert(!wr_iot_dns_config_port("main",&port));
 put("hash#config","port=1055\n");put("main","conf-file=hash#config # trailing comment\n");assert(wr_iot_dns_config_port("main",&port)&&port==1055);assert(!unlink("hash#config"));
 put("main","port=1053#invalid\n");port=999;assert(!wr_iot_dns_config_port("main",&port)&&port==999);
 put("main","txt-record=name,\"value # literal\"\nport=1056\n");assert(wr_iot_dns_config_port("main",&port)&&port==1056);
 put("main","txt-record=name,\"unterminated\nport=1056\n");port=999;assert(!wr_iot_dns_config_port("main",&port)&&port==999);
 put("quoted ,#file","port=1057\n");put("main","conf-file=\"quoted ,#file\" # comment\n");assert(wr_iot_dns_config_port("main",&port)&&port==1057);assert(!unlink("quoted ,#file"));
 put("main","port=\"1058\"\n");assert(wr_iot_dns_config_port("main",&port)&&port==1058);
 assert(!mkdir("dir ,#quoted",0700));put("dir ,#quoted/one.conf","port=1059\n");put("main","conf-dir=\"dir ,#quoted\",*.conf\n");assert(wr_iot_dns_config_port("main",&port)&&port==1059);assert(!unlink("dir ,#quoted/one.conf"));assert(!rmdir("dir ,#quoted"));
 {char final_quote[]="port=\"1060\"";assert(wr_iot_dns_config_comments(final_quote));}
 put("\ttabbed\t","port=1061\n");put("main","conf-file=\"\\ttabbed\\t\"\n");assert(wr_iot_dns_config_port("main",&port)&&port==1061);assert(!unlink("\ttabbed\t"));
 put("quote\"file","port=1062\n");put("main","conf-file=\"quote\\\"file\"\n");assert(wr_iot_dns_config_port("main",&port)&&port==1062);assert(!unlink("quote\"file"));
 {int dhcp4=99;
  put("main","port=0\ndhcp-range=set:wr-iot,192.168.50.20,192.168.50.200,255.255.255.0,3600\n");assert(wr_iot_dns_config_services("main",&port,&dhcp4)&&port==0&&dhcp4==1);
  put("main","dhcp-range=set:ipv6,::,constructor:br0,ra-stateless\n");assert(wr_iot_dns_config_services("main",&port,&dhcp4)&&port==53&&dhcp4==0);
  put("extra","dhcp-range=tag:known,set:lan,192.168.1.20,192.168.1.200,3600\n");put("main","conf-file=extra\n");assert(wr_iot_dns_config_services("main",&port,&dhcp4)&&dhcp4==1);
  put("main","dhcp-range=lan,192.168.1.20,192.168.1.200,3600\n");assert(wr_iot_dns_config_services("main",&port,&dhcp4)&&dhcp4==1);
  put("main","port=65536\n");port=999;dhcp4=99;assert(!wr_iot_dns_config_services("main",&port,&dhcp4)&&port==999&&dhcp4==99);
 }
 assert(!mkdir("additional",0700));put("additional/b.conf","port=1054\n");put("additional/a.conf","port=1053\n");put("additional/.hidden","port=65536\n");put("additional/c.bak","port=65536\n");
 put("main","conf-dir=additional,*.conf,.bak\n");assert(wr_iot_dns_config_port("main",&port)&&port==1054);
 assert(!unlink("additional/a.conf"));assert(!unlink("additional/b.conf"));assert(!unlink("additional/.hidden"));assert(!unlink("additional/c.bak"));assert(!rmdir("additional"));
 assert(!symlink("extra","link"));assert(!wr_iot_dns_config_port("link",&port));assert(!unlink("link"));
 assert(!unlink("main"));assert(!unlink("extra"));assert(!chdir("/tmp"));assert(!rmdir(dir));
 puts("PASS bounded effective DNS port reader: default, nested override, disabled DNS, invalid port, include cycle and symlink rejection; comment boundaries and quoted literals");return 0;
}
