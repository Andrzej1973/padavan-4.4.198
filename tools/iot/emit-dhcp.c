#include "dhcp-write.h"
int main(void){
 if(fputs("port=0\nbind-dynamic\ninterface=br0\ndhcp-range=set:lan,192.168.1.20,192.168.1.200,255.255.255.0,3600\n",stdout)==EOF)return 1;
 if(!wr_iot_dhcp_write(stdout,1,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200","192.168.1.1","255.255.255.0"))return 2;
 return fflush(stdout)?3:0;
}
