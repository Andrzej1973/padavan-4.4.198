#include "bridge.h"
#include <string.h>
int main(int argc,char **argv) {
 struct wr_iot_range lan={0xc0a80100,0xc0a801ff};
 if(argc!=2)return 2;
 if(!strcmp(argv[1],"bss-down"))return wr_iot_bss_set_down()?0:1;
 if(!strcmp(argv[1],"up"))return wr_iot_bridge_set_up(1)?0:1;
 if(!strcmp(argv[1],"down"))return wr_iot_bridge_set_up(0)?0:1;
 if(!strcmp(argv[1],"attach"))return wr_iot_bridge_attach()?0:1;
 if(!strcmp(argv[1],"detach"))return wr_iot_bridge_detach()?0:1;
 if(!strcmp(argv[1],"remove"))return wr_iot_bridge_remove()?0:1;
 if(!strcmp(argv[1],"prepare"))return wr_iot_bridge_prepare("192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1)?0:1;
 return 2;
}
