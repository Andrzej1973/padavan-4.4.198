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
shutdown = '\tinit_cgi(NULL);\n\trelease_dictionary(&kw_XX);\n\trelease_dictionary(&kw_EN);'
if s.count(loop) != 1 or s.count(timeout) != 1 or s.count(shutdown) != 1 or 'wr_device_background_tick' in s:
    raise SystemExit('Background sampling anchors changed; no files written')
s = '#if defined(BOARD_WR1200JS)\nextern void wr_device_background_tick(void);\nextern void wr_device_background_close(void);\n#endif\n' + s
s = s.replace(loop, loop + '\n#if defined(BOARD_WR1200JS)\n\t\twr_device_background_tick();\n#endif', 1)
s = s.replace(timeout, '#if defined(BOARD_WR1200JS)\n\t\ttv.tv_sec = 5;\n#else\n' + timeout + '\n#endif', 1)
s = s.replace(shutdown, '#if defined(BOARD_WR1200JS)\n\twr_device_background_close();\n#endif\n' + shutdown, 1)
f.write_text(s, encoding='utf-8')
print('Prepared WR loop sampling; connection expiry constant unchanged; callback must be linked before enabling workflow')
