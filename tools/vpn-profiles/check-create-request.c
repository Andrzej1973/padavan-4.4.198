#include "web/vpn-create-request.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static const char token[]="0123456789abcdef0123456789abcdef";
static void invalid(const char *id,const char *protocol)
{
    char body[128];struct wr_vpn_create_request parsed;
    int n=snprintf(body,sizeof(body),"%s\n%s\n%s\nx",token,id,protocol);
    assert(n>0 && !wr_vpn_create_parse((unsigned char *)body,(size_t)n,&parsed));
}
int main(void)
{
    unsigned char body[WR_VPN_CREATE_BODY_MAX+1];
    struct wr_vpn_create_request parsed;
    size_t n,i,prefix;
    n=(size_t)snprintf((char *)body,sizeof(body),"%s\n999\namneziawg\n[Interface]\r\n",token);
    assert(wr_vpn_create_parse(body,n,&parsed));
    assert(parsed.id==999 && !strcmp(parsed.token,token));
    assert(!strcmp(parsed.protocol,"amneziawg") && parsed.size==13);
    for(i=0;i<46;i++) assert(!wr_vpn_create_parse(body,i,&parsed));
    invalid("0","wireguard");invalid("01","wireguard");
    invalid("1000","wireguard");invalid("-1","wireguard");
    invalid("1;id","wireguard");invalid("1","WireGuard");
    invalid("1","wireguard\r");invalid("1","unsupported");
    prefix=(size_t)snprintf((char *)body,sizeof(body),"%s\n1\nwireguard\n",token);
    assert(!wr_vpn_create_parse(body,prefix,&parsed));
    memset(body+prefix,'x',WR_VPN_CREATE_CONFIG_MAX);
    assert(wr_vpn_create_parse(body,prefix+WR_VPN_CREATE_CONFIG_MAX,&parsed));
    assert(parsed.size==WR_VPN_CREATE_CONFIG_MAX && parsed.config==body+prefix);
    body[prefix+WR_VPN_CREATE_CONFIG_MAX]='x';
    assert(!wr_vpn_create_parse(body,prefix+WR_VPN_CREATE_CONFIG_MAX+1,&parsed));
    body[prefix]=0;assert(!wr_vpn_create_parse(body,prefix+1,&parsed));
    body[prefix]='x';body[0]='g';assert(!wr_vpn_create_parse(body,prefix+1,&parsed));
    assert(!wr_vpn_create_parse(NULL,100,&parsed));
    assert(!wr_vpn_create_parse(body,prefix+1,NULL));
    puts("PASS VPN create request bounds, protocol/ID/token grammar and binary rejection; no storage or network operations");
    return 0;
}
