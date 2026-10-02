from pathlib import Path
import re
import sys
root = Path(sys.argv[1]) / "trunk"
config = root / "configs/templates/WR1200JS.config"
text = config.read_text()
if "CONFIG_FIRMWARE_INCLUDE_TPROXY=" in text:
    raise SystemExit("TPROXY selector already exists")
config.write_text(text.rstrip() + "\n\n### Include transparent proxy target; no interception rules enabled by default.\nCONFIG_FIRMWARE_INCLUDE_TPROXY=n\n")
source = Path("configs.build/wr1200js.config").read_text().splitlines()
enabled = "CONFIG_FIRMWARE_INCLUDE_TPROXY=y" in source
path = root / "configs/boards/WR1200JS/kernel-4.4.x.config"
lines = path.read_text().splitlines()
key = "CONFIG_NETFILTER_XT_TARGET_TPROXY"
lines = [l for l in lines if not l.startswith(key + "=") and l != "# " + key + " is not set"]
lines.append(key + "=m" if enabled else "# " + key + " is not set")
if enabled:
    values = dict(l.split("=", 1) for l in lines if l.startswith("CONFIG_") and "=" in l)
    for dependency in ("CONFIG_NETFILTER_XT_MATCH_SOCKET", "CONFIG_NF_DEFRAG_IPV4"):
        if values.get(dependency) not in ("y", "m"):
            raise SystemExit("Missing TPROXY dependency: " + dependency)
path.write_text("\n".join(lines) + "\n")
print("TPROXY selector follows requested config; runtime firewall rules unchanged")
