#!/usr/bin/env python3
"""Exercise actual runtime unit/header preparation without repository includes."""
from pathlib import Path
from types import SimpleNamespace
import ast
import json
import runpy
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
shared = here.parent / "band-steering"
text = (here / "prepare-runtime.py").read_text()
tree = ast.parse(text)
once = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "once")
snapshot_code = text[text.index("try:\n snapshot="):text.index("\ndef once")]
units_code = text[text.index("common=('status-channel'"):text.index("for target,data in pending.items()")]
with tempfile.TemporaryDirectory(prefix="wr-config-stage-") as directory:
    cases=[(False,False),(True,False)]+([(True,True)] if len(sys.argv)>1 else [])
    for prepared,flash in cases:
        root = Path(directory) / (str(prepared)+str(flash))
        trunk = root / "trunk"
        rc, http = trunk / "user/rc", trunk / "user/httpd"
        for parent, role in ((rc, "server"), (http, "client")):
            (parent / "wr-iot").mkdir(parents=True)
            (parent / "Makefile").write_text("OBJS += wr-iot-control-mailbox.o wr-iot-control-" + role + ".o\n")
            for header in here.glob("*.h"):
                (parent / "wr-iot" / header.name).write_bytes(header.read_bytes())
            (parent / "shared-wifi").mkdir()
            (parent / "shared-wifi/validate.h").write_bytes((here.parent / "shared-wifi/validate.h").read_bytes())
        (rc / "rc.h").write_text("int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\nconst char *nvram_safe_get(const char *);\nint get_ap_mode(void);\nint get_enabled_radio_rt(void);\nint is_radio_on_rt(void);\nint get_mode_radio_rt(void);\n")
        producer=ast.parse((here/'prepare-rc.py').read_text())
        selector=next(ast.literal_eval(n.value) for n in producer.body if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id=='include' for t in n.targets))
        (rc/'ralink.c').write_text(selector)
        if prepared:
            kernel = trunk / "linux-4.4.x"
            native = kernel / "drivers/nvram/nvram.c"
            native.parent.mkdir(parents=True)
            native.write_bytes((here / "fixtures/config-native-getall.c").read_bytes())
            (kernel / ".config").write_text("# CONFIG_MTD_NAND_MTK is not set\n")
            native_header = kernel / "include/nvram/bcmnvram.h"
            native_header.parent.mkdir(parents=True)
            native_header.write_bytes((here / "fixtures/config-bcmnvram.h").read_bytes())
            (trunk / ".config").write_text("CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y\n")
            with (rc / "Makefile").open("a") as f:
                f.write("OBJS += wr-band-settings-snapshot.o\n")
            (rc / "wr-band-settings-snapshot.c").write_bytes((shared / "settings-snapshot.c").read_bytes().replace(
                b'"settings-snapshot.h"', b'"wr-band-settings-snapshot.h"'))
            (rc / "wr-band-settings-snapshot.h").write_bytes((shared / "settings-snapshot.h").read_bytes())
            subprocess.run([sys.executable, str(shared / "prepare-nvram-snapshot.py"),
                            "--kernel-root", str(kernel)], check=True)
        if flash:
            ordered=runpy.run_path(str(shared/'prepare-nvram-commit-order.py'))['prepare'](Path(sys.argv[1]).read_text())
            staged=runpy.run_path(str(shared/'prepare-nvram-flash-readback.py'))['prepare'](ordered)
            (kernel/'drivers/nvram/nvram_linux.c').write_text(staged)
            (kernel/'drivers/nvram/wr-nvram-flash-wire.h').write_bytes((here/'native-flash-wire.h').read_bytes())
        scope = {"local": here, "rc": rc, "http": http, "runpy": runpy, "json": json,
                 "a": SimpleNamespace(source=root, native_trunk=trunk if prepared else None)}
        exec(compile(ast.Module(body=[once], type_ignores=[]), "<actual once helper>", "exec"), scope)
        exec(compile(snapshot_code, "<actual snapshot preparation>", "exec"), scope)
        exec(compile(units_code, "<actual runtime units preparation>", "exec"), scope)
        assert scope["snapshot"]["verified"] is prepared
        assert scope["flash_readback"]["verified"] is flash
        for path, content in scope["pending"].items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        marker = (rc / "wr-iot/config-snapshot-prepared.h").read_text()
        view_report=json.loads((root/'iot-edit-view-source.json').read_text())
        assert view_report['native_capabilities_verified'] is bool(prepared and flash)
        assert not view_report['http_bound'] and not view_report['target_verified']
        assert "PREPARED " + str(int(prepared)) + "\n" in marker
        for unit in ("native-flash-reader", "flash-save-native"):
            subprocess.run(["make", "-C", str(rc), "ROOTDIR=" + str(trunk),
                            "CC=gcc", "CFLAGS=-std=gnu11 -Wall -Wextra -Werror -O2 -I" + str(rc),
                            "wr-iot-" + unit + ".o"], check=True)
        for unit in ("config-view-runtime", "config-view-channel", "config-view-endpoint", "config-edit-server", "config-server", "config-owner", "saved-config-store", "native-flash-reader", "flash-save-attempt", "flash-save-native", "flash-worker", "config-save-owner", "config-save-server", "cold-on-generation", "radio-on-generation", "restart-generation", "restart-profile", "rc-mode"):
            assert ("wr-iot-" + unit + ".o") in (rc / "Makefile").read_text()
            subprocess.run(["gcc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O2",
                            "-I" + str(rc), "-I"+str(trunk/"linux-4.4.x/include/nvram"), "-fsyntax-only", str(rc / ("wr-iot-" + unit + ".c"))], check=True)
        for unit in ("config-view-client","config-view-channel","config-view-endpoint"):
            assert ("wr-iot-"+unit+".o") in (http/'Makefile').read_text()
            subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(http),
                            '-fsyntax-only',str(http/('wr-iot-'+unit+'.c'))],check=True)
print("PASS actual staged config units: RC object/header mappings and generated prepared0/1 capability compile with isolated includes; pinned native snapshot guard required for1; host only")
