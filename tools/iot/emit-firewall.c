#include "firewall.h"
int main(int argc,char **argv) {
 struct wr_iot_firewall rules;struct wr_iot_range lan={0xc0a80100,0xc0a801ff};const char *fragment;
 if(argc!=2||(strcmp(argv[1],"4")&&strcmp(argv[1],"6")))return 2;
 if(!wr_iot_firewall_plan(&rules,1,"br0","eth2.2","192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",&lan,1))return 3;
 fragment=!strcmp(argv[1],"4")?rules.ipv4:rules.ipv6;
 if(fputs("*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n",stdout)==EOF||
    fputs(fragment,stdout)==EOF||
    fputs("-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT\n-A INPUT -i br0 -j ACCEPT\n-A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT\n-A FORWARD -i br0 -j ACCEPT\nCOMMIT\n",stdout)==EOF)return 4;
 return fflush(stdout)?4:0;
}
