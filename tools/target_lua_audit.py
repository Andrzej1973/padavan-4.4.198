"""Bounded execution of the image Lua converters; no router operations."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def audit_lua(root, qemu, closure, readelf):
    root = Path(root).resolve()
    report = {"selected": True, "passed": False,
              "scope": "image Lua ELF closure, syntax and JSON converter execution under QEMU; service consumers and nixio operations unverified",
              "checks": {}, "scripts": []}
    checks = report["checks"]
    try:
        lua = closure.resolve_image(root, "usr/bin/lua")
        if not lua.stat().st_mode & 0o111:
            raise ValueError("Image Lua is not executable")
        modules = sorted((root / "etc_ro/lua/5.1/lib").glob("*.so"))
        required = {"cjson.so", "nixio.so"}
        if not required.issubset({p.name for p in modules}):
            raise ValueError("Image Lua native modules are missing")
        report["elf_dependency_closure"] = closure.verify(
            root, root, readelf, ["usr/bin/lua"] +
            [p.relative_to(root).as_posix() for p in modules])
        checks["elf_dependency_closure"] = True
        scripts = sorted((root / "etc_ro/lua/5.1/share").rglob("*.lua"))
        if not scripts or len(scripts) > 128:
            raise ValueError("Missing or excessive Lua script inventory")
        # A clean cwd and explicit environment exclude host LUA_PATH/CPath/INIT.
        # QEMU -L maps the guest's compiled /etc_ro module paths into this image.
        with tempfile.TemporaryDirectory(prefix="wr-image-lua-") as tmp:
            def run(args, data=None):
                return subprocess.run(
                    [qemu, "-L", str(root), str(lua), *args], input=data,
                    capture_output=True, timeout=10, cwd=tmp,
                    env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
            version = run(["-v"])
            report["version"] = (version.stdout + version.stderr).decode(errors="replace").strip()
            checks["lua_5_1_version"] = version.returncode == 0 and "Lua 5.1" in report["version"]
            for path in scripts:
                result = run(["-e", 'assert(loadfile(' + json.dumps(str(path)) + '))'])
                report["scripts"].append({"path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "syntax_exit": result.returncode,
                    "error": result.stderr.decode(errors="replace")[:1000] if result.returncode else ""})
            checks["all_lua_syntax"] = all(x["syntax_exit"] == 0 for x in report["scripts"])
            sample = {"name": "router", "enabled": True, "count": 3,
                      "items": [1, "wifi", False], "nested": {"ok": "yes"}}
            converter = root / "etc_ro/lua/5.1/share/json2lua.lua"
            reverse = root / "etc_ro/lua/5.1/share/lua2json.lua"
            first = run([str(converter)], json.dumps(sample).encode())
            second = run([str(reverse)], first.stdout) if first.returncode == 0 else None
            report["conversion"] = {
                "json_to_lua_exit": first.returncode,
                "lua_to_json_exit": second.returncode if second is not None else None,
                "json_to_lua_error": first.stderr.decode(errors="replace")[:1000],
                "lua_to_json_error": second.stderr.decode(errors="replace")[:1000] if second is not None else "not executed"}
            checks["json_to_lua"] = first.returncode == 0 and bool(first.stdout)
            try:
                checks["roundtrip"] = second is not None and second.returncode == 0 and json.loads(second.stdout) == sample
            except (ValueError, UnicodeError):
                checks["roundtrip"] = False
            checks["invalid_json_rejected"] = run([str(converter)], b'{broken').returncode != 0
            checks["invalid_lua_rejected"] = run([str(reverse)], b'{broken').returncode != 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        checks["audit_completed"] = False
    report["passed"] = bool(checks) and all(checks.values())
    return report
