#!/usr/bin/env python3
"""Stage a bounded, escaped cached ZeroTier status reader. Not CI-wired yet."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
root = parser.parse_args().source
backend = root / 'trunk/user/httpd/web_ex.c'
text = backend.read_text(encoding='utf-8')
anchor = 'static int zerotier_status_hook(int eid, webs_t wp, int argc, char **argv)'
hook = r'''/* Read only the monitor's public status cache; never execute CLI in HTTP. */
static int zerotier_cached_status_hook(int eid, webs_t wp, int argc, char **argv)
{
	FILE *status;
	int ch;
	unsigned int count = 0;
	if (!nvram_match("zerotier_enable", "1")) {
		websWrite(wp, "ZeroTier is disabled.");
		return 0;
	}
	status = fopen("/var/run/zerotier-state.txt", "r");
	if (!status) {
		websWrite(wp, "Status is not available yet. Authorize this node in your network controller.");
		return 0;
	}
	while (count < 4096 && (ch = fgetc(status)) != EOF) {
		++count;
		switch (ch) {
		case '&': websWrite(wp, "&amp;"); break;
		case '<': websWrite(wp, "&lt;"); break;
		case '>': websWrite(wp, "&gt;"); break;
		case '"': websWrite(wp, "&quot;"); break;
		case '\'': websWrite(wp, "&#39;"); break;
		default:
			if (ch == '\n' || ch == '\t' || (ch >= 32 && ch <= 126))
				websWrite(wp, "%c", ch);
			else
				websWrite(wp, "?");
		}
	}
	if (count == 4096 && fgetc(status) != EOF)
		websWrite(wp, "\n[Additional status omitted]");
	fclose(status);
	return 0;
}

'''
registration = '\t{ "zerotier_status", zerotier_status_hook},'
if text.count(anchor) != 1 or text.count(registration) != 1:
    raise SystemExit('Pinned ZeroTier HTTP status anchors mismatch')
text = text.replace(anchor, hook + anchor).replace(
    registration, registration + '\n\t{ "zerotier_cached_status", zerotier_cached_status_hook},')
page = root / 'trunk/user/www/n56u_ribbon_fixed/Advanced_zerotier.asp'
web = page.read_text(encoding='utf-8')
anchor = '<td id="zerotier_status" colspan="3"></td>'
if web.count(anchor) != 1:
    raise SystemExit('Pinned ZeroTier WebUI status anchor mismatch')
web = web.replace(anchor, anchor + '''
                                            </tr>
                                            <tr>
                                                <th>Node and network status</th>
                                                <td colspan="3"><pre style="white-space: pre-wrap;">&lt;% zerotier_cached_status(); %&gt;</pre>
                                                <small>Reload this page to refresh. The timestamp shows when the background monitor last updated the cache. Network membership needs authorization in the controller.</small></td>'''.replace('&lt;%', '<%').replace('%&gt;', '%>'))
for path, content in ((backend, text), (page, web)):
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
print('Staged fixed-path escaped cached status hook and WebUI panel')
