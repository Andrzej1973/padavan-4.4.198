#include "network-check.h"
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 return wr_iot_network_services_ready(argv[1])?0:1;
}
