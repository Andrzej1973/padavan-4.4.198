#include "dhcp-write.h"
#include <assert.h>
#include <string.h>
int main(void){FILE *fp=tmpfile();char text[1024];long before;size_t n;assert(fp);
 assert(fputs("interface=br0\n",fp)>=0);before=ftell(fp);
 assert(!wr_iot_dhcp_write(fp,1,"192.168.1.1","255.255.255.0","192.168.1.20","192.168.1.200","192.168.1.1","255.255.255.0"));assert(ftell(fp)==before);
 assert(!wr_iot_dhcp_write(fp,0,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200","192.168.1.1","255.255.255.0"));assert(ftell(fp)==before);
 assert(wr_iot_dhcp_write(fp,1,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200","192.168.1.1","255.255.255.0"));
 assert(!fseek(fp,0,SEEK_SET));n=fread(text,1,sizeof(text)-1,fp);text[n]=0;
 assert(!strncmp(text,"interface=br0\n",14));assert(strstr(text,"interface=br-iot\n"));assert(strstr(text,"dhcp-option=tag:wr-iot,6,192.168.50.1\n"));fclose(fp);
 puts("PASS IoT DHCP writer: main fragment preserved, tagged IoT appended, invalid or AP input rejected before output");return 0;}
