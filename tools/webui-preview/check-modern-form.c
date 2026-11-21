#include <assert.h>
#include <stdio.h>
#include "modern-form.h"
int main(void)
{
 const char *good[]={"wr_modern_guest_version=1&rt_guest_ssid=My+Guest&rt_guest_wpa_psk=secret%26%3B%3D%25","wr_modern_wifi_version=1&rt_ssid=%D0%94%D1%96%D0%BC","wr_modern_guest_version=1&rt_guest_enable=0"};
 for(unsigned int i=0;i<sizeof(good)/sizeof(good[0]);i++)assert(wr_modern_form(good[i],strlen(good[i])));
 const char *bad[]={"","rt_guest_ssid=Guest","wr_modern_guest_version=1&wr_modern_wifi_version=1","wr_modern_guest_version=1&rt_guest_enable=0&rt_guest_enable=1","wr_modern_guest_version=1&rt_guest_ssid=A&r%74_guest_ssid=B","wr_modern_guest_version=1&x=%","wr_modern_guest_version=1&x=%0","wr_modern_guest_version=1&x=%GG","wr_modern_guest_version=1&x=%00","wr_modern_guest_version=1&x=raw;other=1","wr_modern_guest_version=1&","wr_modern_guest_version=1&&x=1","wr_modern_guest_version=1&x","wr_modern_guest_version=1&x=raw\nline","wr_modern_guest_version=1&x%00=1"};
 for(unsigned int i=0;i<sizeof(bad)/sizeof(bad[0]);i++)assert(!wr_modern_form(bad[i],strlen(bad[i])));
 assert(!wr_modern_form(NULL,1));assert(!wr_modern_form(good[0],8193));
 char large[2048]="wr_modern_guest_version=1";
 for(unsigned int i=0;i<64;i++){char field[24];snprintf(field,sizeof(field),"&f%u=value",i);strcat(large,field);}
 assert(!wr_modern_form(large,strlen(large)));
 puts("PASS Modern form admission component: canonical duplicate keys, percent/NUL/delimiter/truncation checks, marker/size/field bounds; not body input integration");return 0;
}
