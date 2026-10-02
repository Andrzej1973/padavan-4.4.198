#!/usr/bin/env python3
"""Adapt existing SQM lifecycle; packaging/configuration are separate steps."""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('target', type=Path)
a = p.parse_args()
root = a.target / 'trunk/user'
net_path = root / 'rc/net.c'
svc_path = root / 'rc/services.c'
rc_path = root / 'rc/rc.c'
wan_path = root / 'rc/net_wan.c'
net = net_path.read_text(encoding='utf-8')
svc = svc_path.read_text(encoding='utf-8')
if svc.count('#include <errno.h>') != 1:
    raise SystemExit('Unexpected service header layout')
svc = svc.replace('#include <errno.h>', '#include <errno.h>\n#include <fcntl.h>\n#include <sys/file.h>')
rc = rc_path.read_text(encoding='utf-8')
wan = wan_path.read_text(encoding='utf-8')
anchor = '\tif (hw_nat_mode == 0)\n\t\treturn 0;'
sfe = '\tint sfe_enable = nvram_get_int("sfe_enable");'
start = '#if defined(APP_SQM)\nvoid stop_sqm(void){'
end = '\n#endif'
boot = '\tnvram_unset("wan_ifname_t");'
wan_up = '\t/* di wakeup after 2 secs */'
wan_down = '\tlogmessage(LOGNAME, "%s %s (%s)", "WAN", "down", wan_ifname);'
if net.count(anchor) != 1 or net.count(sfe) != 1 or svc.count(start) != 1:
    raise SystemExit('Unexpected acceleration/SQM source layout')
if rc.count(boot) != 1 or wan.count(wan_up) != 1 or wan.count(wan_down) != 1:
    raise SystemExit('Unexpected boot/WAN lifecycle layout')
if 'sqm_running_t' in net or 'sqm_running_t' in svc:
    raise SystemExit('SQM lifecycle already adapted')
wrapper = root / 'sqm-qos/scripts/run.sh'
if not wrapper.is_file():
    raise SystemExit('Existing SQM scripts required')
net = net.replace(anchor, anchor + '''
#if defined(APP_SQM)
\t/* Runtime inhibition leaves the user's hardware NAT preference intact. */
\tif (nvram_get_int("sqm_running_t"))
\t\treturn 0;
#endif''')
net = net.replace(sfe, sfe + '''
#if defined(APP_SQM)
\tif (nvram_get_int("sqm_running_t"))
\t\tsfe_enable = 0;
#endif''')
begin = svc.index(start)
finish = svc.index(end, begin) + len(end)
svc = svc[:begin] + '''#if defined(APP_SQM)
static int sqm_lock(void)
{
\tint fd = open("/var/run/wr1200js-sqm.lock", O_CREAT | O_RDWR, 0600);
\tif (fd < 0)
\t\treturn -1;
\tif (fcntl(fd, F_SETFD, FD_CLOEXEC) < 0 || flock(fd, LOCK_EX) < 0) {
\t\tclose(fd);
\t\treturn -1;
\t}
\treturn fd;
}

static int stop_sqm_locked(void)
{
\tif (eval("/usr/lib/sqm/run.sh", "stop") != 0) {
\t\tlogmessage("SQM", "Cleanup failed; acceleration remains inhibited");
\t\treturn 1;
\t}
\tnvram_unset("sqm_running_t");
\treload_nat_modules();
\treturn 0;
}

static void start_sqm_locked(void)
{
\tchar ifname[16];
\tif (nvram_get_int("sqm_enable") != 1 || get_ap_mode())
\t\treturn;
\tif (nvram_get_int("sqm_running_t"))
\t\treturn;
\tget_wan_ifname(ifname);
\tif (!*ifname || !is_interface_exist(ifname))
\t\treturn;
\tnvram_set_temp("sqm_running_t", "1");
\treload_nat_modules();
\t/* Do not start shaping while an acceleration path remains loaded. */
\tif (is_module_loaded("hw_nat") || is_module_loaded("fast_classifier") ||
\t    eval("/usr/lib/sqm/run.sh", "start", ifname) != 0) {
\t\tlogmessage("SQM", "Start failed; cleaning up queues");
\t\tstop_sqm_locked();
\t}
}

void stop_sqm(void)
{
\tint fd = sqm_lock();
\tif (fd < 0) {
\t\tlogmessage("SQM", "Cannot acquire lifecycle lock");
\t\treturn;
\t}
\tstop_sqm_locked();
\tclose(fd);
}

void start_sqm(void)
{
\tint fd = sqm_lock();
\tif (fd < 0) {
\t\tlogmessage("SQM", "Cannot acquire lifecycle lock");
\t\treturn;
\t}
\tstart_sqm_locked();
\tclose(fd);
}

void restart_sqm(void)
{
\tint fd = sqm_lock();
\tif (fd < 0) {
\t\tlogmessage("SQM", "Cannot acquire lifecycle lock");
\t\treturn;
\t}
\tif (stop_sqm_locked() == 0)
\t\tstart_sqm_locked();
\tclose(fd);
}
#endif''' + svc[finish:]
rc = rc.replace(boot, boot + '''
#if defined(APP_SQM)
\tnvram_unset("sqm_running_t");
#endif''')
wan = wan.replace(wan_up, '''#if defined(APP_SQM)
\tif (unit == 0)
\t\trestart_sqm();
#endif

''' + wan_up)
wan = wan.replace(wan_down, wan_down + '''
#if defined(APP_SQM)
\tif (unit == 0)
\t\tstop_sqm();
#endif''')
net_path.write_text(net, encoding='utf-8')
svc_path.write_text(svc, encoding='utf-8')
rc_path.write_text(rc, encoding='utf-8')
wan_path.write_text(wan, encoding='utf-8')
shutil.copyfile(Path(__file__).with_name('run.sh'), wrapper)
print('SQM lifecycle adapted; firmware packaging and runtime verification pending')
