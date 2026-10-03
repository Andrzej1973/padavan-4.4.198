#!/usr/bin/env python3
"""Candidate HTTP second-mask integration; compile/runtime validation pending."""
import argparse
import re
from pathlib import Path

def replace(text, old, new, count=1):
    if text.count(old) != count:
        raise RuntimeError('Inspect event engine anchor: ' + old)
    return text.replace(old, new)

parser = argparse.ArgumentParser()
parser.add_argument('httpd', type=Path)
args = parser.parse_args()
common = args.httpd / 'common.h'
web = args.httpd / 'web_ex.c'
c = common.read_text(encoding='utf-8')
w = web.read_text(encoding='utf-8')
c = replace(c, '\tu64 event_mask;\n};', '\tu64 event_mask;\n\tu64 event_mask_extended;\n};')
c = replace(c, '\tu64 event_unmask;\n};', '\tu64 event_unmask;\n\tu64 event_mask_extended;\n\tu64 event_unmask_extended;\n};')
w = replace(w, 'static u64 restart_needed_bits = 0;', '''static u64 restart_needed_bits = 0;
static u64 restart_needed_extended = 0;
static void request_restart_events(u64 legacy, u64 extended)
{
    restart_needed_bits |= legacy;
    restart_needed_extended |= extended;
}''')
w = replace(w, '\tu64 event_mask;', '\tu64 event_mask;\n\tu64 event_mask_extended;')
w = replace(w, '\t\tevent_mask = v->event_mask & ~(EVM_BLOCK_UNSAFE);', '\t\tevent_mask = v->event_mask & ~(EVM_BLOCK_UNSAFE);\n\t\tevent_mask_extended = v->event_mask_extended;')
old = 'restart_needed_bits |= event_mask;'
if w.count(old) < 1:
    raise RuntimeError('Missing field event accumulation')
w = w.replace(old, 'request_restart_events(event_mask, event_mask_extended);')
w = replace(w, 'if (event_mask) {', 'if (event_mask || event_mask_extended) {')
w = replace(w, 'return (nvram_modified || restart_needed_bits) ? 1 : 0;', 'return (nvram_modified || restart_needed_bits || restart_needed_extended) ? 1 : 0;')
w = replace(w, 'restart_needed_bits |= (v->event_mask & ~(EVM_BLOCK_UNSAFE));', 'request_restart_events(v->event_mask & ~(EVM_BLOCK_UNSAFE), v->event_mask_extended);')
w = replace(w, 'if (restart_needed_bits != 0 &&', 'if ((restart_needed_bits != 0 || restart_needed_extended != 0) &&')
w = replace(w, 'if (!restart_needed_bits)', 'if (!restart_needed_bits && !restart_needed_extended)')
w = replace(w, 'if ((restart_needed_bits & events_desc[i].event_mask) != 0) {', 'if ((restart_needed_bits & events_desc[i].event_mask) != 0 ||\n\t\t    (restart_needed_extended & events_desc[i].event_mask_extended) != 0) {', 2)
w = replace(w, 'restart_needed_bits &= ~events_desc[i].event_unmask;', 'restart_needed_bits &= ~events_desc[i].event_unmask;\n\t\t\trestart_needed_extended &= ~events_desc[i].event_mask_extended;\n\t\t\trestart_needed_extended &= ~events_desc[i].event_unmask_extended;')
reset_pattern = r'^(\t+)restart_needed_bits = 0;$'
if len(re.findall(reset_pattern, w, re.M)) != 4:
    raise RuntimeError('Inspect pending event resets')
w = re.sub(reset_pattern, lambda match: match.group(0) + '\n' + match.group(1) + 'restart_needed_extended = 0;', w, flags=re.M)
# All anchors are validated before either source is changed.
common.write_text(c, encoding='utf-8')
web.write_text(w, encoding='utf-8')
print('Second HTTP event bank transformed; compile/runtime verification pending')
