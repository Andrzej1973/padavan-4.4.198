#!/usr/bin/env python3
"""Reject oversized/incomplete native apply forms before parsing any settings."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('web', type=Path)
args = parser.parse_args()
source = args.web.read_text(encoding='utf-8')
old = '''static void
do_html_apply_post(const char *url, FILE *stream, int clen, char *boundary)
{
	init_cgi(NULL);

	group_del_map[0] = -1;

	post_buf[0] = 0;
	if (!fgets(post_buf, MIN(clen+1, sizeof(post_buf)), stream))
		return;

	clen -= strlen(post_buf);
	while (clen--)
		fgetc(stream);

	websScan(post_buf);
	init_cgi(post_buf);
}'''
new = '''static void
do_html_apply_post(const char *url, FILE *stream, int clen, char *boundary)
{
	size_t received;
	apply_post_rejected = 0;
	init_cgi(NULL);
	group_del_map[0] = -1;
	post_buf[0] = 0;
	if (clen <= 0)
		return;
	if ((size_t)clen >= sizeof(post_buf)) {
		apply_post_rejected = 1;
		while (clen-- > 0 && fgetc(stream) != EOF) { }
		httpd_log("Apply form rejected: encoded body exceeds buffer capacity");
		return;
	}
	received = fread(post_buf, 1, (size_t)clen, stream);
	if (received != (size_t)clen || memchr(post_buf, '\\0', received) != NULL) {
		post_buf[0] = 0;
		apply_post_rejected = 1;
		httpd_log("Apply form rejected: incomplete or invalid encoded body");
		return;
	}
	post_buf[received] = 0;
	websScan(post_buf);
	init_cgi(post_buf);
}'''
if source.count(old) != 1:
    raise SystemExit('Inspect exact native apply input handler before patching')
declaration = 'static char post_buf[65535] = {0};'
reset = '\trestart_needed_bits = 0;\n\trestart_needed_extended = 0;\n\n\t// assign control variables'
if source.count(declaration) != 1 or source.count(reset) != 1:
    raise SystemExit('Inspect request rejection declaration/response hooks')
response = '''\tif (apply_post_rejected) {
\t\tapply_post_rejected = 0;
\t\twebsWrite(wp, "<script>if(parent.hideLoading)parent.hideLoading();parent.alert('The configuration was not saved: the request was too large or incomplete.');</script>\\n");
\t\treturn 0;
\t}

'''
source = source.replace(declaration, 'static int apply_post_rejected = 0;\n' + declaration, 1)
source = source.replace(reset, reset.replace('\t// assign control variables', response + '\t// assign control variables'), 1)
args.web.write_text(source.replace(old, new, 1), encoding='utf-8')
print('Native apply parser now requires a complete body within buffer capacity')
