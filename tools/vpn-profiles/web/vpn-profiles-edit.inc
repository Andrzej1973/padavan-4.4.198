/* Edit a stopped private profile at an expected revision. Never starts a tunnel. */
#include "vpn-edit-request.h"
static unsigned char wr_vpn_edit_body[WR_VPN_EDIT_BODY_MAX];
static size_t wr_vpn_edit_size;
static void wr_vpn_edit_clear(void)
{
    volatile unsigned char *p=wr_vpn_edit_body;
    size_t i;
    for(i=0;i<sizeof(wr_vpn_edit_body);i++)p[i]=0;
    wr_vpn_edit_size=0;
}
static void wr_vpn_edit_input(const char *url,FILE *stream,int clen,char *boundary)
{
    (void)url;(void)boundary;
    wr_vpn_edit_clear();
    if (!get_login_safe() || !wr_vpn_request_is_post() || clen<=0 ||
        (size_t)clen>sizeof(wr_vpn_edit_body)) {
        while(clen-->0)if(fgetc(stream)==EOF)break;
        return;
    }
    if(fread(wr_vpn_edit_body,1,(size_t)clen,stream)==(size_t)clen)
        wr_vpn_edit_size=(size_t)clen;
    else wr_vpn_edit_clear();
}
static void wr_vpn_edit_output(const char *url,FILE *stream)
{
    struct wr_vpn_edit_request r;
    char id[8],revision[24],output[96],expected[64];const char *args[5];int saved=0;
    (void)url;
    if (!get_login_safe() || !wr_vpn_request_is_post()) {
        wr_vpn_edit_clear();websWrite(stream,"{\"error\":\"unsafe_request\"}");return;
    }
    if (!wr_vpn_edit_parse(wr_vpn_edit_body,wr_vpn_edit_size,&r) ||
        !wr_vpn_csrf[0] || strcmp(r.token,wr_vpn_csrf)) {
        wr_vpn_edit_clear();websWrite(stream,"{\"error\":\"invalid_request\"}");return;
    }
    snprintf(id,sizeof(id),"%u",r.id);
    snprintf(revision,sizeof(revision),"%llu",(unsigned long long)r.revision);
    args[0]=WR_VPN_PROFILE_BIN;args[1]="edit";args[2]=id;args[3]=revision;args[4]=NULL;
    snprintf(expected,sizeof(expected),"saved\t%u\t%llu\n",r.id,(unsigned long long)(r.revision+1));
    if (wr_vpn_web_run_input(args,output,sizeof(output),r.config,r.size) &&
        !strcmp(output,expected)) saved=1;
    wr_vpn_edit_clear();
    if(saved)websWrite(stream,"{\"saved\":true,\"started\":false}");
    else websWrite(stream,"{\"error\":\"edit_unconfirmed\"}");
}
