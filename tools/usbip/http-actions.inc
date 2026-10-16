#include "wr-usbip-job.h"
#ifndef WR_USBIP_JOB_DIRECTORY
#define WR_USBIP_JOB_DIRECTORY "/var/run/wr-usbip-jobs"
#endif
static char wr_usbip_csrf[33];
static int wr_usbip_post_seen;
static pid_t wr_usbip_http_worker;
extern int wr_usbip_request_is_post(void);

static int ej_wr_usbip_token(int eid,webs_t wp,int argc,char **argv)
{
 int fd,i;ssize_t got;unsigned char random[16];
 (void)eid;(void)argv;
 if(argc||!get_login_safe())return websWrite(wp,"\"\"");
 if(!wr_usbip_csrf[0]){
  fd=open("/dev/urandom",O_RDONLY);if(fd<0)return websWrite(wp,"\"\"");
  got=read(fd,random,sizeof(random));close(fd);
  if(got!=(ssize_t)sizeof(random))return websWrite(wp,"\"\"");
  for(i=0;i<16;i++)snprintf(wr_usbip_csrf+i*2,3,"%02x",random[i]);
 }
 return websWrite(wp,"\"%s\"",wr_usbip_csrf);
}
static void wr_usbip_action_input(const char *url,FILE *stream,int clen,char *boundary)
{
 wr_usbip_post_seen=0;
 if(clen<=0||clen>1024){while(clen-->0)if(fgetc(stream)==EOF)break;init_cgi(NULL);return;}
 do_html_apply_post(url,stream,clen,boundary);
 wr_usbip_post_seen=1;
}
static void wr_usbip_action_output(const char *url,FILE *stream)
{
 char id[33];int posted=wr_usbip_post_seen;
 const char *token,*action,*bus,*vendor,*product,*serial;
 (void)url;wr_usbip_post_seen=0;
 if(!posted||!wr_usbip_request_is_post()||!get_login_safe()){websWrite(stream,"{\"error\":\"unsafe_request\"}");return;}
 token=websGetVar(stream,"token","");
 if(!wr_usbip_csrf[0]||strlen(token)!=32||strcmp(token,wr_usbip_csrf)||
    strcmp(websGetVar(stream,"ack",""),"1")){
  websWrite(stream,"{\"error\":\"invalid_token_or_confirmation\"}");return;
 }
 action=websGetVar(stream,"operation","");bus=websGetVar(stream,"busid","");
 vendor=websGetVar(stream,"vendor","");product=websGetVar(stream,"product","");
 serial=websGetVar(stream,"serial_hex","");
 {size_t n=strlen(serial),j;
  if(n>512 || n%2){websWrite(stream,"{\"error\":\"invalid_request\"}");return;}
  for(j=0;j<n;j++)if(!strchr("0123456789abcdef",serial[j])){
   websWrite(stream,"{\"error\":\"invalid_request\"}");return;
  }
 }
 if(!wr_usbip_job_args(action,bus,vendor,product)){
  websWrite(stream,"{\"error\":\"invalid_request\"}");return;
 }
 if(!wr_usbip_job_reap(&wr_usbip_http_worker)||
    !wr_usbip_job_start_serial(WR_USBIP_JOB_DIRECTORY,action,bus,vendor,product,serial,id,&wr_usbip_http_worker)){
  websWrite(stream,"{\"error\":\"busy_or_unavailable\"}");return;
 }
 websWrite(stream,"{\"accepted\":true,\"id\":\"%s\"}",id);
}
static int ej_wr_usbip_job_state(int eid,webs_t wp,int argc,char **argv)
{
 struct wr_usbip_job_result result;
 (void)eid;wr_usbip_job_reap(&wr_usbip_http_worker);
 if(argc!=1||!get_login_safe())return websWrite(wp,"{\"error\":\"unsafe_request\"}");
 if(!wr_usbip_job_read(WR_USBIP_JOB_DIRECTORY,argv[0],wr_usbip_job_now(),120,&result))
  return websWrite(wp,"{\"error\":\"unknown_result\"}");
 return websWrite(wp,"{\"id\":\"%s\",\"state\":%u,\"code\":%d}",result.id,result.state,result.code);
}
