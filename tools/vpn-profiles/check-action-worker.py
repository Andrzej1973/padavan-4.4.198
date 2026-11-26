#!/usr/bin/env python3
"""Host test for the detached profile action worker."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--work", type=Path, help="pre-created work directory (Windows local runs)")
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
here = Path(__file__).resolve().parent


def checks(root: Path) -> None:
    fake = root / "manager"
    service = root / "service"
    actions = root / "actions"
    exe = root / "worker"
    sync_calls = root / "dns-sync-calls"
    subprocess.run(
        [
            "gcc", "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-g",
            "-fsanitize=address,undefined",
            '-DWR_VPN_MANAGER="%s"' % fake,
            '-DWR_VPN_SERVICE="%s"' % service,
            '-DWR_VPN_ACTION_ROOT="%s"' % actions,
            "-DWR_VPN_ACTION_TIMEOUT_MS=300",
            str(here / "action-worker.c"), "-o", str(exe),
        ],
        check=True,
    )
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=1:exitcode=98",
               UBSAN_OPTIONS="halt_on_error=1:exitcode=97")

    def script(body: str) -> None:
        fake.write_text("#!/bin/sh\n" + body + "\n")
        fake.chmod(0o700)

    def dns_service(exit_code: int = 0) -> None:
        service.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "%s"\nexit %d\n' %
                           ("%s", sync_calls, exit_code))
        service.chmod(0o700)

    def clear_sync_calls() -> None:
        sync_calls.write_text("")

    def run(argv, expected: int) -> None:
        result = subprocess.run([str(exe), *argv], capture_output=True, timeout=10, env=env)
        assert result.returncode == expected, (argv, result.returncode, result.stderr)

    def state(profile: int) -> str:
        return (actions / str(profile)).read_bytes().decode("utf-8", "replace")

    record = root / "args.txt"
    dns_service()
    clear_sync_calls()
    script('printf "%%s\\n" "$*" > "%s"; printf "up 1 done\\n"; exit 0' % record)
    run(["1", "up", "192.168.20.0/24"], 0)
    assert record.read_text().strip() == "up 1 192.168.20.0/24"
    text = state(1)
    assert "state=done" in text and "code=0" in text and "output=up 1 done" in text
    assert sync_calls.read_text().strip() == "dns-sync"

    clear_sync_calls()
    script('printf "%%s\\n" "$*" > "%s"; exit 7' % record)
    run(["1", "down", "192.168.20.0/24"], 1)
    assert record.read_text().strip() == "down 1"
    text = state(1)
    assert "state=failed" in text and "code=7" in text
    assert sync_calls.read_text().strip() == "dns-sync"

    clear_sync_calls()
    script("sleep 2")
    run(["2", "up", "192.168.20.0/24"], 1)
    assert "state=timeout" in state(2)
    assert sync_calls.read_text().strip() == "dns-sync"

    clear_sync_calls()
    script("head -c 5000 /dev/zero | tr '\\0' x")
    run(["3", "delete"], 1)
    assert "state=overflow" in state(3)
    assert sync_calls.read_text().strip() == "dns-sync"

    dns_service(1)
    clear_sync_calls()
    script('printf "up 4 done\\n"; exit 0')
    run(["4", "up"], 1)
    text=state(4)
    assert "state=failed" in text and "code=12" in text
    assert "dnsmasq DNS sync failed" in text
    assert sync_calls.read_text().splitlines()==["dns-sync"]*3, sync_calls.read_text()
    dns_service()

    run(["0", "up"], 2)
    run(["1000", "up"], 2)
    run(["1", "frobnicate"], 2)
    run(["1", "up", "bad;cmd"], 2)
    puts = "PASS profile action worker: argv, done/failed/timeout/overflow state and invalid input"
    print(puts)


if args.work:
    checks(args.work)
else:
    with tempfile.TemporaryDirectory(prefix="wrvpn-action-") as temporary:
        checks(Path(temporary))
