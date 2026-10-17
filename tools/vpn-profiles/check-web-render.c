#include "web/vpn-profiles-render.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    char rows[1024];
    assert(wr_vpn_web_render("1\tWG1\t2\n2\tAWG2\t5\n",rows,sizeof(rows))==1);
    assert(strstr(rows,"<td>1</td><td>WG1</td><td>2</td><td><button type=\"button\""));
    assert(strstr(rows,"<td>2</td><td>AWG2</td><td>5</td><td><button type=\"button\""));
    assert(strstr(rows,"onclick=\"wrVPNAct('up',1)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNAct('down',2)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNAct('delete',1)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNQr(1)\"")!=NULL);
    assert(wr_vpn_web_render("",rows,sizeof(rows))==0);
    assert(wr_vpn_web_render("garbage\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tbad label\t2\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tWG1\t0\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1000\tWG1\t2\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tWG1\t2\nbad\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tWG1\t2\n",rows,8)==-1);
    puts("PASS VPN web render: exact rows, empty list and malformed/truncated refusal");
    return 0;
}
