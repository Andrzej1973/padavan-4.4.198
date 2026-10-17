#ifndef WR_VPN_WEB_RENDER_H
#define WR_VPN_WEB_RENDER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
static inline int wr_vpn_web_render(const char *output,char *rows,size_t capacity)
{
    const char *line=output;size_t used=0;int count=0;
    if (!output || !rows || capacity<2) return -1;
    while (line && *line) {
        const char *nl=strchr(line,'\n');
        size_t length=nl?(size_t)(nl-line):strlen(line);
        char row[400];int written;
        if (length) {
            const char *tab1=memchr(line,'\t',length);
            const char *tab2=tab1?memchr(tab1+1,'\t',length-(size_t)(tab1+1-line)):NULL;
            unsigned int id;unsigned long long revision;char *end;
            if (!tab1 || !tab2) return -1;
            id=(unsigned int)strtoul(line,&end,10);
            if (end!=tab1 || id<1 || id>999) return -1;
            if (!wr_vpn_web_label(tab1+1,(size_t)(tab2-(tab1+1)))) return -1;
            revision=strtoull(tab2+1,&end,10);
            if (end!=(nl?nl:line+length) || !revision) return -1;
            written=snprintf(row,sizeof(row),
                "<tr><td>%u</td><td>%.*s</td><td>%llu</td>"
                "<td><button type=\"button\" class=\"btn btn-mini\" onclick=\"wrVPNAct('up',%u)\">Up</button> "
                "<button type=\"button\" class=\"btn btn-mini\" onclick=\"wrVPNAct('down',%u)\">Down</button> "
                "<button type=\"button\" class=\"btn btn-mini\" onclick=\"wrVPNAct('delete',%u)\">Delete</button>"
                "</td></tr>\n",
                id,(int)(tab2-(tab1+1)),tab1+1,revision,id,id,id);
            if (written<0 || (size_t)written>=sizeof(row) ||
                used+(size_t)written>=capacity) return -1;
            memcpy(rows+used,row,(size_t)written);used+=(size_t)written;
            count++;
        }
        line=nl?nl+1:NULL;
    }
    if (!count) return 0;
    rows[used]=0;
    return 1;
}

#endif
