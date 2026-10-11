#!/usr/bin/env python3
"""Prepare WR event-loop sampling independently of browser requests."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
f = a.source / 'trunk/user/httpd/httpd.c'
s = f.read_text(encoding='utf-8')
loop = '\twhile (!daemon_exit) {\n\t\tfd_set rfds;'
timeout = '\t\ttv.tv_sec = MAX_CONN_TIMEOUT;'
expiry = '\t\t/* check and accept new connection */\n'
shutdown = '\tinit_cgi(NULL);\n\trelease_dictionary(&kw_XX);\n\trelease_dictionary(&kw_EN);'
if s.count(loop) != 1 or s.count(timeout) != 1 or s.count(expiry) != 1 or s.count(shutdown) != 1 or 'wr_device_background_tick' in s:
    raise SystemExit('Background sampling anchors changed; no files written')
if not s.index(loop) < s.index(timeout) < s.index(expiry):
    raise SystemExit('Select timeout no longer precedes connection handling; no files written')
s = '#if defined(BOARD_WR1200JS)\nextern void wr_device_background_tick(void);\nextern void wr_device_background_close(void);\nstatic long wr_device_idle_since;\n#endif\n' + s
s = s.replace(loop, loop + '\n#if defined(BOARD_WR1200JS)\n\t\twr_device_background_tick();\n#endif', 1)
s = s.replace(timeout, '#if defined(BOARD_WR1200JS)\n\t\ttv.tv_sec = 5;\n#else\n' + timeout + '\n#endif', 1)
# A select timeout closes every accepted connection that has not sent its
# request. Upstream reaches it after MAX_CONN_TIMEOUT without socket activity;
# the 5 s sampling wakeups must not shorten that expiry.
s = s.replace(expiry, '#if defined(BOARD_WR1200JS)\n'
              '\t\tif (selected)\n\t\t\twr_device_idle_since = uptime();\n'
              '\t\telse if (uptime() - wr_device_idle_since < MAX_CONN_TIMEOUT)\n\t\t\tcontinue;\n'
              '#endif\n' + expiry, 1)
s = s.replace(shutdown, '#if defined(BOARD_WR1200JS)\n\twr_device_background_close();\n#endif\n' + shutdown, 1)
f.write_text(s, encoding='utf-8')
print('Prepared WR 5 s loop sampling; idle connections still expire after MAX_CONN_TIMEOUT without activity')
