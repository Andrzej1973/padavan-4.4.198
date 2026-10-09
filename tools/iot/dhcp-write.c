#include "dhcp-write.h"
#include "dhcp.h"
int wr_iot_dhcp_write(FILE *fp,int router_mode,const char *gateway,const char *mask,
 const char *start,const char *end,const char *lan_ip,const char *lan_mask) {
 char fragment[512];uint32_t address,netmask,inverse;struct wr_iot_range lan;
 if(!fp||!wr_iot_ipv4(lan_ip,&address)||!wr_iot_ipv4(lan_mask,&netmask))return 0;
 inverse=~netmask;if(inverse&(inverse+1))return 0;
 lan.first=address&netmask;lan.last=lan.first|inverse;
 if(!wr_iot_dhcp_fragment(fragment,sizeof(fragment),1,router_mode,gateway,mask,start,end,&lan,1))return 0;
 return fputs(fragment,fp)>=0&&!ferror(fp);
}
