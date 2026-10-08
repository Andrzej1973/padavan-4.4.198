/* Insert these rules BEFORE every generic ESTABLISHED/LAN accept, including defaults. */
#ifndef WR_IOT_FIREWALL_H
#define WR_IOT_FIREWALL_H
#include "subnet.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
struct wr_iot_firewall {char ipv4[8192],ipv6[256];};
static int wr_iot_fw_append(char *out,size_t capacity,const char *format,...) {
 size_t used=strlen(out);int n;va_list args;
 va_start(args,format);n=vsnprintf(out+used,capacity-used,format,args);va_end(args);
 return n>=0&&(size_t)n<capacity-used;
}
static int wr_iot_fw_ifname(const char *s) {
 size_t i,n;if(!s)return 0;n=strlen(s);if(!n||n>15)return 0;
 for(i=0;i<n;i++)if(!((s[i]>='a'&&s[i]<='z')||(s[i]>='A'&&s[i]<='Z')||
    (s[i]>='0'&&s[i]<='9')||s[i]=='_'||s[i]=='.'||s[i]=='-'))return 0;
 return strcmp(s,"br-iot")!=0;
}
static void wr_iot_fw_address(char out[16],uint32_t v) {
 snprintf(out,16,"%u.%u.%u.%u",(unsigned)(v>>24),(unsigned)((v>>16)&255),
  (unsigned)((v>>8)&255),(unsigned)(v&255));
}
static int wr_iot_firewall_plan(struct wr_iot_firewall *out,int enabled,const char *lan,const char *wan,
 const char *gateway,const char *mask,const char *start,const char *end,
 const struct wr_iot_range *reserved,size_t count) {
 struct wr_iot_firewall candidate;struct wr_iot_subnet p;
 char g[16],net[16],m[16],first[16],last[16];size_t i;
 static const char *const blocked[]={"0.0.0.0/8","10.0.0.0/8","100.64.0.0/10","127.0.0.0/8",
 "169.254.0.0/16","172.16.0.0/12","192.168.0.0/16","224.0.0.0/4","240.0.0.0/4"};
 if(!out)return 0;
 memset(&candidate,0,sizeof(candidate));
 if(!enabled){*out=candidate;return 1;}
 if(count>16||!wr_iot_fw_ifname(lan)||!wan||
    (*wan&&(!wr_iot_fw_ifname(wan)||!strcmp(lan,wan)))||
    !wr_iot_subnet_plan(&p,gateway,mask,start,end,reserved,count))return 0;
 wr_iot_fw_address(g,p.gateway);wr_iot_fw_address(net,p.network);wr_iot_fw_address(m,p.mask);
#define ADD(...) do {if(!wr_iot_fw_append(candidate.ipv4,sizeof(candidate.ipv4),__VA_ARGS__))return 0;} while(0)
 ADD("-A INPUT -i br-iot -m state --state INVALID -j DROP\n");
 ADD("-A INPUT -i br-iot -s 0.0.0.0/32 -d 255.255.255.255/32 -p udp --sport 68 --dport 67 -j ACCEPT\n");
 ADD("-A INPUT -i br-iot ! -s %s/%s -j DROP\n",net,m);
 ADD("-A INPUT -i br-iot -d %s -p udp --sport 68 --dport 67 -j ACCEPT\n",g);
 ADD("-A INPUT -i br-iot -d 255.255.255.255/32 -p udp --sport 68 --dport 67 -j ACCEPT\n");
 ADD("-A INPUT -i br-iot -d %s -p udp --dport 53 -j ACCEPT\n",g);
 ADD("-A INPUT -i br-iot -d %s -p tcp --dport 53 -j ACCEPT\n",g);
 ADD("-A INPUT -i br-iot -j DROP\n");
 ADD("-A FORWARD -i br-iot -m state --state INVALID -j DROP\n");
 ADD("-A FORWARD -o br-iot -m state --state INVALID -j DROP\n");
 ADD("-A FORWARD -i br-iot ! -s %s/%s -j DROP\n",net,m);
 ADD("-A FORWARD -o br-iot ! -d %s/%s -j DROP\n",net,m);
 for(i=0;i<count;i++) {
  wr_iot_fw_address(first,reserved[i].first);wr_iot_fw_address(last,reserved[i].last);
  ADD("-A FORWARD -i br-iot -m iprange --dst-range %s-%s -j DROP\n",first,last);
 }
 for(i=0;i<sizeof(blocked)/sizeof(blocked[0]);i++)ADD("-A FORWARD -i br-iot -d %s -j DROP\n",blocked[i]);
 if(*wan) {
  ADD("-A FORWARD -i br-iot -o %s -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT\n",wan);
  ADD("-A FORWARD -i %s -o br-iot -m state --state ESTABLISHED,RELATED -j ACCEPT\n",wan);
 }
 ADD("-A FORWARD -i br-iot -j DROP\n-A FORWARD -o br-iot -j DROP\n");
#undef ADD
 /* IPv6 remains blocked until a dedicated isolated IPv6 policy is implemented. */
 strcpy(candidate.ipv6,"-A INPUT -i br-iot -j DROP\n-A FORWARD -i br-iot -j DROP\n-A FORWARD -o br-iot -j DROP\n");
 *out=candidate;return 1;
}
#endif
