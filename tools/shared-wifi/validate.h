/* Pure shared Wi-Fi validation. No NVRAM writes, allocation or logging. */
#ifndef WR_SHARED_WIFI_VALIDATE_H
#define WR_SHARED_WIFI_VALIDATE_H
#include <stddef.h>
#include <string.h>
struct wr_shared_wifi_fields {
 const char *ssid, *auth, *wep, *wpa_mode, *crypto, *password;
};
enum wr_shared_wifi_result {
 WR_SHARED_WIFI_OK=0, WR_SHARED_WIFI_SSID, WR_SHARED_WIFI_SECURITY,
 WR_SHARED_WIFI_PASSWORD, WR_SHARED_WIFI_MISSING
};
/* Strict UTF-8: reject overlong encodings, surrogates and values above U+10FFFF. */
static int wr_shared_wifi_text(const char *s, size_t min, size_t max) {
 size_t n,i=0; unsigned int cp; unsigned char c; int need,j;
 if (!s) return 0;
 n=strlen(s); if(n<min || n>max) return 0;
 while(i<n) {
  c=(unsigned char)s[i++];
  if(c<0x20 || c==0x7f) return 0;
  if(c<0x80) continue;
  if(c>=0xc2 && c<=0xdf){cp=c&0x1f;need=1;}
  else if(c>=0xe0 && c<=0xef){cp=c&0x0f;need=2;}
  else if(c>=0xf0 && c<=0xf4){cp=c&7;need=3;}
  else return 0;
  if(i+(size_t)need>n) return 0;
  for(j=0;j<need;j++){c=(unsigned char)s[i++];if((c&0xc0)!=0x80)return 0;cp=(cp<<6)|(c&0x3f);}
  if((need==1 && cp<0x80)||(need==2 && cp<0x800)||(need==3 && cp<0x10000)||
     (cp>=0xd800 && cp<=0xdfff)||cp>0x10ffff)return 0;
 }
 return 1;
}
static int wr_shared_wifi_psk(const char *s) {
 size_t i;
 if(!s)return 0;
 if(strlen(s)!=64)return wr_shared_wifi_text(s,8,63);
 for(i=0;i<64;i++)if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f')||(s[i]>='A'&&s[i]<='F')))return 0;
 return 1;
}
static enum wr_shared_wifi_result wr_shared_wifi_validate(const struct wr_shared_wifi_fields *f) {
 if(!f || !f->ssid || !f->auth || !f->wep)return WR_SHARED_WIFI_MISSING;
 if(!wr_shared_wifi_text(f->ssid,1,32))return WR_SHARED_WIFI_SSID;
 if(strcmp(f->wep,"0"))return WR_SHARED_WIFI_SECURITY;
 if(!strcmp(f->auth,"open"))return WR_SHARED_WIFI_OK;
 if(strcmp(f->auth,"psk"))return WR_SHARED_WIFI_SECURITY;
 if(!f->wpa_mode || !f->crypto || !f->password)return WR_SHARED_WIFI_MISSING;
 if(strcmp(f->wpa_mode,"0") && strcmp(f->wpa_mode,"1") && strcmp(f->wpa_mode,"2"))return WR_SHARED_WIFI_SECURITY;
 if(strcmp(f->crypto,"aes") && strcmp(f->crypto,"tkip") && strcmp(f->crypto,"tkip+aes"))return WR_SHARED_WIFI_SECURITY;
 if(!wr_shared_wifi_psk(f->password))return WR_SHARED_WIFI_PASSWORD;
 return WR_SHARED_WIFI_OK;
}
#endif
