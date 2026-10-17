#ifndef WR_VPN_WEB_RENDER_H
#define WR_VPN_WEB_RENDER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

static int wr_vpn_web_label(const char *text,size_t length)
{
    size_t i;
    if (!length || length>=16) return 0;
    for (i=0;i<length;i++) {
        char c=text[i];
        if (!((c>='0'&&c<='9')||(c>='A'&&c<='Z')||(c>='a'&&c<='z'))) return 0;
    }
    return 1;
}

/* Renders "id<TAB>label<TAB>revision" lines as table rows. Returns 1 with
 * rows, 0 when the list is empty, and -1 when any line is malformed or the
 * output would be truncated (no partial table is ever returned). */
static inline int wr_vpn_web_render_window(const char *output,char *rows,size_t capacity,
                                          unsigned int offset,unsigned int limit,unsigned int *total)
{
    const char *line=output;size_t used=0;int count=0;
    struct {const char *label;size_t length;unsigned long long revision;} entries[1000];
    unsigned int id,ordinal=0;
    if (!output || !rows || capacity<2) return -1;
    memset(entries,0,sizeof(entries));rows[0]=0;
    while (line && *line) {
        const char *nl=strchr(line,'\n');
        size_t length=nl?(size_t)(nl-line):strlen(line);
        if (length) {
            const char *tab1=memchr(line,'\t',length);
            const char *tab2=tab1?memchr(tab1+1,'\t',length-(size_t)(tab1+1-line)):NULL;
            unsigned long long revision;char *end;const char *p;
            if (!tab1 || !tab2) return -1;
            if (tab1-line>3 || line[0]<'1' || line[0]>'9') return -1;
            id=(unsigned int)strtoul(line,&end,10);
            if (end!=tab1 || id<1 || id>999 || entries[id].label) return -1;
            if (!wr_vpn_web_label(tab1+1,(size_t)(tab2-(tab1+1)))) return -1;
            for(p=tab2+1;p<line+length;p++)if(*p<'0'||*p>'9')return -1;
            errno=0;
            revision=strtoull(tab2+1,&end,10);
            if (errno || end!=(nl?nl:line+length) || !revision) return -1;
            entries[id].label=tab1+1;entries[id].length=(size_t)(tab2-(tab1+1));
            entries[id].revision=revision;
            count++;
        }
        line=nl?nl+1:NULL;
    }
    if(total)*total=(unsigned int)count;
    for(id=1;id<=999;id++) {
        char row[896];int written;
        if(entries[id].label) {
            unsigned int current=ordinal++;
            if(current<offset || current-offset>=limit)continue;
            written=snprintf(row,sizeof(row),
                "<tr><td>%u</td><td>%.*s</td><td>%llu</td>"
                "<td><button type=\"button\" class=\"btn btn-mini\" onclick=\"wrVPNQr(%u)\">QR</button> "
                "<button type=\"button\" class=\"btn btn-mini wr-vpn-up\" onclick=\"wrVPNAct('up',%u)\">Up</button> "
                "<button type=\"button\" class=\"btn btn-mini wr-vpn-down\" onclick=\"wrVPNAct('down',%u)\">Down</button> "
                "<button type=\"button\" class=\"btn btn-mini wr-vpn-delete\" onclick=\"wrVPNAct('delete',%u)\">Delete</button>"
                " <button type=\"button\" class=\"btn btn-mini wr-vpn-observe\" onclick=\"wrVPNObserve(%u,this)\">?</button>"
                " <span id=\"wr_vpn_link_%u\" role=\"status\">?</span>"
                "</td></tr>\n",
                id,(int)entries[id].length,entries[id].label,entries[id].revision,id,id,id,id,id,id);
            if (written<0 || (size_t)written>=sizeof(row) ||
                used+(size_t)written>=capacity) return -1;
            memcpy(rows+used,row,(size_t)written);used+=(size_t)written;
        }
    }
    rows[used]=0;
    return used?1:0;
}

static inline int wr_vpn_web_render(const char *output,char *rows,size_t capacity)
{ return wr_vpn_web_render_window(output,rows,capacity,0,999,NULL); }

#endif
