/* Authenticated one-shot export of one stored profile. The response carries
 * the private configuration, so it is a POST behind the CSRF token, marked
 * no-cache, and never written to disk or logged. */
#ifndef WR_VPN_EXPORT_MAX
#define WR_VPN_EXPORT_MAX 16384u
#endif

static void wr_vpn_export_input(const char *url,FILE *stream,int clen,char *boundary)
{
    wr_vpn_post_seen=0;
    if (clen<=0 || clen>512) { while (clen-->0) if (fgetc(stream)==EOF) break; init_cgi(NULL); return; }
    do_html_apply_post(url,stream,clen,boundary);
    wr_vpn_post_seen=1;
}

static void wr_vpn_export_output(const char *url,FILE *stream)
{
    unsigned int id;int posted=wr_vpn_post_seen;
    const char *token,*idtext;char idarg[16];const char *args[4];
    char *raw,*json;size_t used=0,i;
    (void)url;wr_vpn_post_seen=0;
    if (!posted || !wr_vpn_request_is_post() || !get_login_safe()) {
        websWrite(stream,"{\"error\":\"unsafe_request\"}");return;
    }
    token=websGetVar(stream,"token","");
    if (!wr_vpn_csrf[0] || strlen(token)!=32 || strcmp(token,wr_vpn_csrf) ||
        strcmp(websGetVar(stream,"ack",""),"1")) {
        websWrite(stream,"{\"error\":\"invalid_token_or_confirmation\"}");return;
    }
    idtext=websGetVar(stream,"id","");
    if (!wr_vpn_action_id(idtext,&id)) { websWrite(stream,"{\"error\":\"invalid_request\"}");return; }
    raw=malloc(WR_VPN_EXPORT_MAX+2);
    json=malloc((size_t)WR_VPN_EXPORT_MAX*6+64);
    if (!raw || !json) {
        free(raw);free(json);
        websWrite(stream,"{\"error\":\"unavailable\"}");return;
    }
    snprintf(idarg,sizeof(idarg),"%u",id);
    args[0]=WR_VPN_PROFILE_BIN;args[1]="export";args[2]=idarg;args[3]=NULL;
    if (!wr_vpn_web_run(args,raw,WR_VPN_EXPORT_MAX+2)) {
        memset(raw,0,WR_VPN_EXPORT_MAX+2);
        free(raw);free(json);
        websWrite(stream,"{\"error\":\"unavailable\"}");return;
    }
    for (i=0;raw[i] && used+8<((size_t)WR_VPN_EXPORT_MAX*6+64);i++) {
        unsigned char c=(unsigned char)raw[i];
        if (c=='"') { json[used++]='\\';json[used++]='"'; }
        else if (c=='\\') { json[used++]='\\';json[used++]='\\'; }
        else if (c=='\n') { json[used++]='\\';json[used++]='n'; }
        else if (c=='\r') { json[used++]='\\';json[used++]='r'; }
        else if (c=='\t') { json[used++]='\\';json[used++]='t'; }
        else if (c<0x20) {
            static const char hex[]="0123456789abcdef";
            json[used++]='\\';json[used++]='u';json[used++]='0';json[used++]='0';
            json[used++]=hex[(c>>4)&0xf];json[used++]=hex[c&0xf];
        } else json[used++]=(char)c;
    }
    json[used]=0;
    memset(raw,0,WR_VPN_EXPORT_MAX+2);
    free(raw);
    websWrite(stream,"{\"config\":\"%s\"}",json);
    memset(json,0,used);
    free(json);
}
