#!/usr/bin/env python3
"""Candidate routing of four Privoxy editors to persistent storage."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('web', type=Path)
args = parser.parse_args()
s = args.web.read_text(encoding='utf-8')
if 'privoxy_file_allowed' in s or 'event_mask_extended' not in s:
    raise SystemExit('Inspect Privoxy file routing/extended bank')
helper = '''#if defined(APP_PRIVOXY)
static int privoxy_file_allowed(const char *name)
{
    return !strcmp(name, "config") || !strcmp(name, "user.action") ||
           !strcmp(name, "user.filter") || !strcmp(name, "user.trust");
}
static int privoxy_dump_textarea(webs_t wp, const char *filename)
{
    FILE *fp = fopen(filename, "r");
    int ch, result = 0;
    if (!fp) return 0;
    while ((ch = fgetc(fp)) != EOF) {
        if (ch == '&') result += websWrite(wp, "%s", "&amp;");
        else if (ch == '<') result += websWrite(wp, "%s", "&lt;");
        else if (ch == '>') result += websWrite(wp, "%s", "&gt;");
        else result += websWrite(wp, "%c", ch);
    }
    fclose(fp);
    return result;
}
#endif

'''
anchor = 'static u64 restart_needed_bits = 0;'
if s.count(anchor) != 1:
    raise SystemExit('Inspect helper insertion')
s = s.replace(anchor, helper + anchor, 1)
anchor = '\telse if (strncmp(file, "scripts.", 8)==0)'
if s.count(anchor) != 1:
    raise SystemExit('Inspect file dump routing')
branch = '''#if defined(APP_PRIVOXY)
    else if (strncmp(file, "privoxy.", 8)==0) {
        if (!get_login_safe() || !privoxy_file_allowed(file+8))
            return 0;
        snprintf(filename, sizeof(filename), "%s/%s", "/etc/storage/privoxy", file+8);
        return privoxy_dump_textarea(wp, filename);
    }
#endif
'''
s = s.replace(anchor, branch + anchor, 1)
anchor = '\t\t\t} else if (!strncmp(v->name, "scripts.", 8)) {'
if s.count(anchor) != 1:
    raise SystemExit('Inspect file save routing')
branch = '''            }
#if defined(APP_PRIVOXY)
            else if (!strncmp(v->name, "privoxy.", 8)) {
                if (get_login_safe() && privoxy_file_allowed(file_name) &&
                    write_textarea_to_file(value, "/etc/storage/privoxy", file_name)) {
                    request_restart_events(event_mask, event_mask_extended);
                    need_mtd_write = 1;
                }
            }
#endif
            else if (!strncmp(v->name, "scripts.", 8)) {'''
s = s.replace(anchor, branch, 1)
args.web.write_text(s, encoding='utf-8')
print('Privoxy editor file routing added; runtime validation pending')
