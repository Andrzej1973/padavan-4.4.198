#include "web/vpn-profiles-render.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    char rows[2048];
    assert(wr_vpn_web_render("1\tWG1\t2\n2\tAWG2\t5\n",rows,sizeof(rows))==1);
    assert(strstr(rows,"<td>1</td><td>WG1</td><td>2</td><td><button type=\"button\""));
    assert(strstr(rows,"<td>2</td><td>AWG2</td><td>5</td><td><button type=\"button\""));
    assert(strstr(rows,"onclick=\"wrVPNAct('up',1)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNAct('down',2)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNAct('delete',1)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNQr(1)\"")!=NULL);
    assert(strstr(rows,"onclick=\"wrVPNObserve(1,this)\"")!=NULL);
    assert(strstr(rows,"id=\"wr_vpn_link_2\"")!=NULL);
    assert(wr_vpn_web_render("",rows,sizeof(rows))==0);
    assert(wr_vpn_web_render("garbage\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tbad label\t2\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tWG1\t0\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1000\tWG1\t2\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tWG1\t2\nbad\n",rows,sizeof(rows))==-1);
    assert(wr_vpn_web_render("1\tWG1\t2\n",rows,8)==-1);
    {
        char metadata[49152],page[9000];size_t used=0;unsigned int total=0,id;
        for(id=999;id;id--)used+=(size_t)snprintf(metadata+used,sizeof(metadata)-used,"%u\tWG%u\t1\n",id,id);
        assert(wr_vpn_web_render_window(metadata,page,sizeof(page),0,10,&total)==1 && total==999);
        assert(strstr(page,"<td>1</td><td>WG1</td>") && strstr(page,"<td>10</td><td>WG10</td>"));
        assert(!strstr(page,"<td>11</td><td>WG11</td>"));
        assert(wr_vpn_web_render_window(metadata,page,sizeof(page),990,10,&total)==1);
        assert(strstr(page,"<td>991</td><td>WG991</td>") && strstr(page,"<td>999</td><td>WG999</td>"));
        assert(wr_vpn_web_render_window(metadata,page,sizeof(page),999,10,&total)==0);
        assert(wr_vpn_web_render_window("1\tWG1\t1\n1\tWG1\t2\n",page,sizeof(page),0,10,&total)==-1);
        assert(wr_vpn_web_render("1\tWG1\t18446744073709551616\n",rows,sizeof(rows))==-1);
    }
    puts("PASS VPN web render: exact rows, empty list and malformed/truncated refusal");
    return 0;
}
