/* Create a validated private record only. Never starts a tunnel. */
#include "vpn-create-request.h"
static unsigned char wr_vpn_create_body[WR_VPN_CREATE_BODY_MAX];
static size_t wr_vpn_create_size;
static void wr_vpn_create_clear(void)
{
    volatile unsigned char *p=wr_vpn_create_body;
    size_t i;
    for(i=0;i<sizeof(wr_vpn_create_body);i++)p[i]=0;
    wr_vpn_create_size=0;
}
static void wr_vpn_create_input(const char *url,FILE *stream,int clen,char *boundary)
{
    (void)url;(void)boundary;
    wr_vpn_create_clear();
    if (!get_login_safe() || !wr_vpn_request_is_post() || clen<=0 ||
        (size_t)clen>sizeof(wr_vpn_create_body)) {
        while(clen-->0)if(fgetc(stream)==EOF)break;
        return;
    }
    if(fread(wr_vpn_create_body,1,(size_t)clen,stream)==(size_t)clen)
        wr_vpn_create_size=(size_t)clen;
    else wr_vpn_create_clear();
}
static void wr_vpn_create_output(const char *url,FILE *stream)
{
    struct wr_vpn_create_request r;
    char id[8],output[96],expected[64];const char *args[5];int saved=0;
    (void)url;
    if (!get_login_safe() || !wr_vpn_request_is_post()) {
        wr_vpn_create_clear();websWrite(stream,"{\"error\":\"unsafe_request\"}");return;
    }
    if (!wr_vpn_create_parse(wr_vpn_create_body,wr_vpn_create_size,&r) ||
        !wr_vpn_csrf[0] || strcmp(r.token,wr_vpn_csrf)) {
        wr_vpn_create_clear();websWrite(stream,"{\"error\":\"invalid_request\"}");return;
    }
    snprintf(id,sizeof(id),"%u",r.id);
    args[0]=WR_VPN_PROFILE_BIN;args[1]="create";args[2]=id;args[3]=r.protocol;args[4]=NULL;
    snprintf(expected,sizeof(expected),"saved\t%u\t1\n",r.id);
    if (wr_vpn_web_run_input(args,output,sizeof(output),r.config,r.size) &&
        !strcmp(output,expected)) saved=1;
    wr_vpn_create_clear();
    if(saved)websWrite(stream,"{\"saved\":true,\"started\":false}");
    else websWrite(stream,"{\"error\":\"create_unconfirmed\"}");
}
