#!/usr/bin/env python3
"""Exercise the shipped VPN profile service wrapper under the image BusyBox."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("romfs", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = args.romfs.resolve()
busybox = root / "bin/busybox"
service = root / "usr/sbin/wr-vpn-profiles-service"
qemu = shutil.which("qemu-mipsel-static") or shutil.which("qemu-mipsel")
if not qemu:
    raise SystemExit("target QEMU is required")
if not busybox.is_file() or not service.is_file():
    raise SystemExit("target BusyBox or VPN profile service is missing")

report = {
    "scope": "VPN profile wrapper lock path under image BusyBox with fake commands; no network mutation",
    "runtime_verified": False,
    "checks": {},
}

with tempfile.TemporaryDirectory(prefix="wr-vpn-target-service-") as temp:
    work = Path(temp)
    fakebin = work / "bin"
    fakebin.mkdir()
    calls = work / "calls.log"
    lock = work / "service.lock"
    run_dir = work / "run"
    dns_dir = work / "dns"

    def executable(name, body):
        path = fakebin / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o755)
        return path

    executable("nvram", '''
case "$2" in
  wrvpn_enabled) printf '7\\n';;
  wrvpn_protect) printf '192.168.20.0/24\\n';;
  wrvpn_use_dns) printf '1\\n';;
  *) exit 1;;
esac
''')
    executable("logger", "exit 0\n")
    executable("killall", "exit 0\n")
    executable("flock", '''
printf '%s\\n' "$*" >> "$WRVPN_TEST_FLOCK_LOG"
exit 0
''')
    control = executable("wr-vpn-profile", '''
printf '%s\\n' "$*" >> "$WRVPN_TEST_CONTROL_LOG"
if [ "$1" = down ]; then
    rm -f "$WRVPN_RUN_DIR/$2/wrv$2.dns"
fi
''')

    env = os.environ.copy()
    env.update({
        "PATH": os.pathsep.join((str(fakebin), "/usr/bin", "/bin")),
        "WRVPN_CTL": str(control),
        "WRVPN_LOCK": str(lock),
        "WRVPN_RUN_DIR": str(run_dir),
        "WRVPN_DNS_DIR": str(dns_dir),
        "WRVPN_TEST_FLOCK_LOG": str(work / "flock.log"),
        "WRVPN_TEST_CONTROL_LOG": str(calls),
    })
    profile_dir = run_dir / "7"
    profile_dir.mkdir(parents=True)
    profile_dns = profile_dir / "wrv7.dns"
    profile_dns.write_text("192.0.2.53\n2001:db8::53\n", encoding="ascii")
    result = subprocess.run(
        [qemu, "-L", str(root), str(busybox), "sh", str(service), "start"],
        capture_output=True, timeout=15, env=env,
    )
    flock_log = work / "flock.log"
    checks = {
        "target_shell_start_succeeds": result.returncode == 0 and not result.stderr,
        "lock_command_runs_under_target_shell": flock_log.is_file()
            and flock_log.read_text(encoding="utf-8").splitlines() == ["-x -n 9"],
        "lock_file_is_private": lock.exists() and stat.S_IMODE(lock.stat().st_mode) == 0o600,
        "only_requested_profile_is_started": calls.is_file()
            and calls.read_text(encoding="utf-8").splitlines() == ["up 7 192.168.20.0/24"],
    }

    dns_output = dns_dir / "wrvpn.servers"
    checks["start_publishes_profile_dns"] = (
        dns_output.read_text(encoding="ascii") == "server=192.0.2.53\nserver=2001:db8::53\n"
        and stat.S_IMODE(dns_output.stat().st_mode) == 0o644
    )

    stopped = subprocess.run(
        [qemu, "-L", str(root), str(busybox), "sh", str(service), "stop"],
        capture_output=True, timeout=15, env=env,
    )
    checks["target_shell_stop_succeeds"] = stopped.returncode == 0 and not stopped.stderr
    checks["only_requested_profile_is_stopped"] = (
        calls.is_file() and calls.read_text(encoding="utf-8").splitlines()
        == ["up 7 192.168.20.0/24", "down 7"]
    )

    checks["stop_clears_profile_dns"] = dns_output.read_bytes() == b""

    # Without flock available, fail closed before invoking the profile control.
    no_flock = work / "no-flock"
    no_flock.mkdir()
    missing_calls = work / "missing-control.log"
    env.update({
        "PATH": str(no_flock),
        "WRVPN_LOCK": str(work / "missing.lock"),
        "WRVPN_TEST_CONTROL_LOG": str(missing_calls),
    })
    missing = subprocess.run(
        [qemu, "-L", str(root), str(busybox), "sh", str(service), "start"],
        capture_output=True, timeout=15, env=env,
    )
    checks["missing_lock_tool_fails_closed"] = (
        missing.returncode != 0
        and b"flock is required" in missing.stderr
        and not missing_calls.exists()
    )
    report["checks"] = checks
    report["target_busybox_sha256"] = hashlib.sha256(busybox.read_bytes()).hexdigest()
    report["service_sha256"] = hashlib.sha256(service.read_bytes()).hexdigest()
    report["errors"] = {
        "stop_stderr": stopped.stderr.decode(errors="replace"),
        "start_stderr": result.stderr.decode(errors="replace"),
        "missing_flock_stderr": missing.stderr.decode(errors="replace"),
    }

args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
failed = [name for name, passed in report["checks"].items() if not passed]
if failed:
    raise SystemExit("target BusyBox VPN service checks failed: " + ", ".join(failed))
print("PASS VPN profile service lock path under exact target BusyBox; fake controls only, no network mutation")
