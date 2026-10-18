#include "web/vpn-edit-request.h"
#include <assert.h>
#include <stdio.h>
static int parse(const char *revision)
{
    char body[256];struct wr_vpn_edit_request result;
    int n=snprintf(body,sizeof(body),"0123456789abcdef0123456789abcdef\n1\n%s\nx",revision);
    return wr_vpn_edit_parse((const unsigned char *)body,(size_t)n,&result);
}
int main(void)
{
    unsigned char body[WR_VPN_EDIT_BODY_MAX+1];
    struct wr_vpn_edit_request result;size_t prefix;
    assert(parse("1") && parse("18446744073709551614"));
    assert(!parse("0") && !parse("01") && !parse("-1") && !parse("+1"));
    assert(!parse("18446744073709551615") && !parse("18446744073709551616"));
    assert(!parse("") && !parse("1x") && !parse("1\r"));
    prefix=(size_t)snprintf((char *)body,sizeof(body),"0123456789abcdef0123456789abcdef\n999\n12\n");
    assert(!wr_vpn_edit_parse(body,prefix,&result));
    memset(body+prefix,'x',WR_VPN_CREATE_CONFIG_MAX+1);
    assert(wr_vpn_edit_parse(body,prefix+WR_VPN_CREATE_CONFIG_MAX,&result));
    assert(result.id==999 && result.revision==12 && result.config==body+prefix);
    assert(!wr_vpn_edit_parse(body,prefix+WR_VPN_CREATE_CONFIG_MAX+1,&result));
    body[prefix]=0;assert(!wr_vpn_edit_parse(body,prefix+1,&result));
    assert(!wr_vpn_edit_parse(NULL,100,&result));
    puts("PASS edit request canonical revisions, overflow, bounds and binary rejection");
    return 0;
}
