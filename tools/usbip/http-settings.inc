#include "wr-usbip/export-settings.h"
static char wr_usbip_settings_body[32769];
static int wr_usbip_settings_post;
static int wr_usbip_hex_digit(int ch)
{
 if(ch>='0'&&ch<='9')return ch-'0';
 if(ch>='a'&&ch<='f')return ch-'a'+10;
 return -1;
}
static void wr_usbip_settings_input(const char *url,FILE *stream,int length,char *boundary)
{
 size_t used=0,i;(void)url;(void)boundary;
 wr_usbip_settings_post=0;init_cgi(NULL);
 if(length<=0||length>32768){while(length-->0)if(fgetc(stream)==EOF)break;return;}
 while(used<(size_t)length){
  size_t n=fread(wr_usbip_settings_body+used,1,(size_t)length-used,stream);
  if(!n)return;
  used+=n;
 }
 wr_usbip_settings_body[used]=0;if(strlen(wr_usbip_settings_body)!=used)return;
 for(i=0;i<used;i++)if(wr_usbip_settings_body[i]=='%'){
  if(i+2>=used||!isxdigit((unsigned char)wr_usbip_settings_body[i+1])||
     !isxdigit((unsigned char)wr_usbip_settings_body[i+2])||
     (wr_usbip_settings_body[i+1]=='0'&&wr_usbip_settings_body[i+2]=='0'))return;
  i+=2;
 }
 init_cgi(wr_usbip_settings_body);wr_usbip_settings_post=1;
}
static void wr_usbip_settings_output(const char *url,FILE *stream)
{
 const char *token,*encoded;size_t n,i;char *text=NULL;
 struct wr_usbip_export_rule *rules=NULL;enum wr_usbip_store_result result;
 int posted=wr_usbip_settings_post;(void)url;wr_usbip_settings_post=0;
 if(!posted||!wr_usbip_request_is_post()||!get_login_safe()){
  websWrite(stream,"{\"error\":\"unsafe_request\"}");return;
 }
 token=websGetVar(stream,"token","");
 if(!wr_usbip_csrf[0]||strlen(token)!=32||strcmp(token,wr_usbip_csrf)||
    strcmp(websGetVar(stream,"ack",""),"1")){
  websWrite(stream,"{\"error\":\"invalid_token_or_confirmation\"}");return;
 }
 encoded=websGetVar(stream,"table_hex","");n=strlen(encoded);
 if(!n||n%2||n>=2*WR_USBIP_EXPORT_TEXT_MAX)goto invalid;
 text=malloc(n/2);rules=calloc(16,sizeof(*rules));if(!text||!rules)goto invalid;
 for(i=0;i<n;i+=2){
  int high=wr_usbip_hex_digit((unsigned char)encoded[i]),low=wr_usbip_hex_digit((unsigned char)encoded[i+1]);
  if(high<0||low<0)goto invalid;
  text[i/2]=(char)((high<<4)|low);
 }
 if(!wr_usbip_export_decode(text,n/2,rules))goto invalid;
 result=wr_usbip_settings_save(rules);free(text);free(rules);
 if(result==WR_USBIP_STORE_REFUSED){websWrite(stream,"{\"error\":\"refused_or_busy\",\"saved\":false}");return;}
 websWrite(stream,"{\"saved\":true,\"synchronized\":%s,\"applied\":false,\"flash_committed\":false}",
  result==WR_USBIP_STORE_SAVED?"true":"false");return;
invalid:
 free(text);free(rules);websWrite(stream,"{\"error\":\"invalid_or_unavailable\",\"saved\":false}");
}
static int ej_wr_usbip_export_settings(int eid,webs_t wp,int argc,char **argv)
{
 struct wr_usbip_export_rule *rules;char *text;size_t i;enum wr_usbip_settings_state state;
 (void)eid;(void)argv;
 if(argc||!get_login_safe())return websWrite(wp,"{\"error\":\"unsafe_request\"}");
 rules=calloc(16,sizeof(*rules));text=malloc(WR_USBIP_EXPORT_TEXT_MAX);
 if(!rules||!text){free(rules);free(text);return websWrite(wp,"{\"state\":0}");}
 state=wr_usbip_settings_read(rules);
 websWrite(wp,"{\"state\":%d",(int)state);
 if((state==WR_USBIP_SETTINGS_READY||state==WR_USBIP_SETTINGS_EMPTY)&&
    wr_usbip_export_encode(rules,text,WR_USBIP_EXPORT_TEXT_MAX)){
  websWrite(wp,",\"table_hex\":\"");
  for(i=0;text[i];i++)websWrite(wp,"%02x",(unsigned char)text[i]);
  websWrite(wp,"\"");
 }
 free(text);free(rules);return websWrite(wp,"}");
}
