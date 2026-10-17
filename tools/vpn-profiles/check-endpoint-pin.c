#include "endpoint-pin.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static int resolve(const char *host,char *out,size_t size)
{
    const char *answer=NULL;
    if (!strcmp(host,"vpn.example")) answer="203.0.113.9";
    else if (!strcmp(host,"v6.example")) answer="2001:db8::9";
    if (!answer) return 0;
    return snprintf(out,size,"%s",answer)>0;
}

static void expect(const char *input,enum wr_vpn_pin_result code,const char *output)
{
    struct wr_vpn_record in,out;
    memset(&in,0,sizeof(in));memset(&out,0,sizeof(out));
    in.id=7;in.protocol=WR_VPN_WIREGUARD;in.revision=3;
    in.size=strlen(input);memcpy(in.config,input,in.size);
    assert(wr_vpn_pin_endpoints(&in,resolve,&out)==code);
    if (output) {
        assert(out.size==strlen(output));
        assert(!memcmp(out.config,output,out.size));
    }
    assert(out.id==7 && out.protocol==WR_VPN_WIREGUARD && out.revision==3);
}

int main(void)
{
    /* Numeric endpoints stay untouched, byte for byte. */
    expect("[Interface]\nEndpoint = 203.0.113.7:51820\n",
           WR_VPN_PIN_UNCHANGED,"[Interface]\nEndpoint = 203.0.113.7:51820\n");
    expect("Endpoint=198.51.100.4:51820\n",
           WR_VPN_PIN_UNCHANGED,"Endpoint=198.51.100.4:51820\n");
    expect("Endpoint = [2001:db8::1]:51820\n",
           WR_VPN_PIN_UNCHANGED,"Endpoint = [2001:db8::1]:51820\n");

    /* Hostnames are replaced, and the rest of the file is preserved. */
    expect("[Peer]\nEndpoint = vpn.example:51820\nAllowedIPs = 0.0.0.0/0\n",
           WR_VPN_PIN_DONE,
           "[Peer]\nEndpoint = 203.0.113.9:51820\nAllowedIPs = 0.0.0.0/0\n");
    expect("Endpoint = v6.example:51820\n",
           WR_VPN_PIN_DONE,"Endpoint = [2001:db8::9]:51820\n");
    expect("endpoint= vpn.example:51821\n",
           WR_VPN_PIN_DONE,"endpoint= 203.0.113.9:51821\n");

    /* Every peer is pinned, not only the first one. */
    expect("[Peer]\nEndpoint = vpn.example:51820\n[Peer]\nEndpoint = v6.example:51821\n",
           WR_VPN_PIN_DONE,
           "[Peer]\nEndpoint = 203.0.113.9:51820\n[Peer]\nEndpoint = [2001:db8::9]:51821\n");

    /* Refusals leave the caller nothing to apply. */
    expect("Endpoint = bad.example:51820\n",WR_VPN_PIN_UNRESOLVED,NULL);
    expect("Endpoint = vpn.example\n",WR_VPN_PIN_REJECTED,NULL);
    expect("Endpoint = :51820\n",WR_VPN_PIN_REJECTED,NULL);
    expect("Endpoint = [2001:db8::1]51820\n",WR_VPN_PIN_REJECTED,NULL);

    puts("PASS endpoint pinning: numeric untouched, hostname and IPv6 pinned, "
         "resolver refusal and malformed lines rejected; no DNS performed");
    return 0;
}
