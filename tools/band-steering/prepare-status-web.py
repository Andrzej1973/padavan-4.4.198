#!/usr/bin/env python3
"""Expose integer-only steering observations through the authenticated update route."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source', type=Path)
a=p.parse_args()
f=a.source/'trunk/user/httpd/web_ex.c'
s=f.read_text(encoding='utf-8')
anchor='struct ej_handler ej_handlers[] =\n'
entry='\t{ "json_system_status", ej_system_status_hook},\n'
if s.count(anchor)!=1 or s.count(entry)!=1 or 'ej_wr_band_observation' in s:
 raise ValueError('Status web anchors changed; no file written')
code=r'''
#ifdef APP_WR_BAND_STEERING
/* refresh schedules rc only; callers must await a changed observation serial.
 * State 2 means last verified OFF, not a new driver readback. */
static int ej_wr_band_observation(int eid, webs_t wp, int argc, char **argv)
{
 (void)eid;
 int serial = nvram_get_int("wr_bs_observation_serial");
 int state = nvram_get_int("wr_bs_observation");
 int apply = nvram_get_int("wr_bs_apply_state");
 if (serial != nvram_get_int("wr_bs_observation_serial")) {
  serial = 0; state = 0; apply = 0;
 }
 if (serial < 0) serial = 0;
 if (state < 0 || state > 2) state = 0;
 if (apply < 0 || apply > 5) apply = 0;
 if (argc == 1 && !strcmp(argv[0], "refresh"))
  notify_rc("observe_wr_band_steering");
 return websWrite(wp, "{\"serial\":%d,\"observation\":%d,\"apply\":%d}",
                  serial, state, apply);
}
#endif
'''
s=s.replace(anchor,code+'\n'+anchor)
s=s.replace(entry,entry+'#ifdef APP_WR_BAND_STEERING\n\t{ "wr_band_observation", ej_wr_band_observation},\n#endif\n')
f.write_text(s,encoding='utf-8')
print('Added integer-only status response; refresh schedules rc, no Wi-Fi restart')
