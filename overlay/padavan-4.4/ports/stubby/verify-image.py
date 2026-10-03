#!/usr/bin/env python3
"""Verify Stubby ROMFS packaging and ELF dependencies, not runtime DNS behavior."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trunk", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    romfs = args.trunk.resolve() / "romfs"
    checks = {}
    details = {}

    def target_file(name):
        # Resolve absolute links as router paths, never as host filesystem paths.
        parts = list(Path(name.lstrip("/")).parts)
        current = romfs
        hops = 0
        while parts:
            part = parts.pop(0)
            if part == "..":
                current = current.parent
                if current != romfs and romfs not in current.parents:
                    raise RuntimeError("ROMFS path escaped root")
                continue
            current = current / part
            if current.is_symlink():
                hops += 1
                if hops > 40:
                    raise RuntimeError("ROMFS symlink loop")
                link = os.readlink(current)
                current = romfs if link.startswith("/") else current.parent
                parts = list(Path(link.lstrip("/")).parts) + parts
        return current

    try:
        config = (args.trunk / ".config").read_text()
        checks["effective_selector"] = "CONFIG_FIRMWARE_INCLUDE_STUBBY=y" in config.splitlines()
        binary = target_file("/usr/sbin/stubby")
        data = binary.read_bytes()
        checks["mips_elf"] = len(data) >= 20 and data[:4] == b"\x7fELF" and data[5] == 1 and int.from_bytes(data[18:20], "little") == 8
        checks["binary_executable"] = bool(binary.stat().st_mode & 0o111)
        helper = target_file("/usr/bin/stubby.sh").read_text()
        checks["explicit_config"] = '-C "$STUBBY_CONFIG" -g' in helper
        checks["helper_executable"] = bool(target_file("/usr/bin/stubby.sh").stat().st_mode & 0o111)
        checks["serialized_lifecycle"] = "flock -x -n 9" in helper and "9>&-" in helper
        page = target_file("/www/Advanced_Services_DoT.asp").read_text()
        checks["webui"] = "found_app_stubby()" in page and "if (!login_safe())" in page
        resolvers = json.loads(target_file("/www/dot.json").read_text())
        checks["resolver_list"] = isinstance(resolvers, list) and bool(resolvers)
        httpd = target_file("/usr/sbin/httpd").read_bytes()
        checks["httpd_fields"] = b"stubby_enable" in httpd and b"stubby_server_ip3" in httpd
        checks["httpd_capability"] = b"found_app_stubby" in httpd
        rc = target_file("/sbin/rc").read_bytes()
        checks["rc_dispatcher"] = b"restart_stubby" in rc and b"/usr/bin/stubby.sh" in rc
        busybox_config = (args.trunk / "user/busybox/busybox-1.24.x/.config").read_text()
        checks["busybox_prerequisites"] = all("CONFIG_" + key + "=y" in busybox_config.splitlines()
            for key in ["MKTEMP", "FLOCK", "PIDOF", "AWK", "ASH"])

        queue = [binary]
        visited = set()
        missing = []
        dependencies = {}
        while queue:
            elf = queue.pop()
            if elf in visited:
                continue
            visited.add(elf)
            dynamic = subprocess.check_output(["readelf", "-d", str(elf)], text=True)
            needed = re.findall(r"\(NEEDED\).*\[([^\]]+)\]", dynamic)
            dependencies[str(elf.relative_to(romfs))] = needed
            for soname in needed:
                candidates = [target_file(prefix + soname) for prefix in ["/lib/", "/usr/lib/"]]
                dependency = next((path for path in candidates if path.is_file()), None)
                if dependency is None:
                    missing.append(soname)
                else:
                    queue.append(dependency)
        program = subprocess.check_output(["readelf", "-l", str(binary)], text=True)
        interpreters = re.findall(r"Requesting program interpreter:\s*([^\]]+)", program)
        checks["loader"] = len(interpreters) == 1 and target_file(interpreters[0]).is_file()
        checks["shared_library_closure"] = not missing
        details.update(dependencies=dependencies, missing_libraries=sorted(set(missing)), interpreters=interpreters)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        checks["inspection_completed"] = False
        details["error"] = str(error)
    report = {"scope": "Stubby ROMFS packaging and ELF closure; target runtime unverified", "checks": checks, "details": details}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("Stubby image checks failed: " + ", ".join(failed))
    print("Stubby ROMFS and ELF dependency checks passed; runtime remains unverified")


if __name__ == "__main__":
    main()

