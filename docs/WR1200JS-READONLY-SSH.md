# Read-only WR1200JS SSH helper

The helper `tools/wr1200js-readonly.ps1` provides a fixed allowlist of device
inspection commands. It always targets `ASUS@192.168.20.1:22`, uses the local
Windows OpenSSH key at `%USERPROFILE%\.ssh\id_ed25519`, disables TTY and port
forwarding, and accepts only the named `-Check` values in the script. It never
reads, prints, copies or uploads private-key contents. No command changes
router configuration or service state.

Run it from an ordinary Windows PowerShell session, outside the Codex
executor, from any directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work\tools\wr1200js-readonly.ps1" -Check identity
```

Allowed checks are: `identity`, `uptime`, `mtd`, `pci`, `interfaces`,
`modules`, `radio-ownership`, `wifi-commands`, `wifi-stats`, `wifi-show`, `temperature-paths`,
and `txbf-log`. Replace `identity` with one of those values to run that
single fixed inspection.

`radio-ownership` lists the fixed ra0/ra1/ra2/rai0/rai1 sysfs links and their
device/driver/module links, plus mt76x3_ap/mt76x2_ap holders and refcnt files.
It does not load/unload modules or change interface state. Missing sysfs links
remain visible in output and are not proof that a driver has no ownership.
An empty holders directory or low reference count does not establish unload
safety, radio quiescence, or absence of hardware/DMA activity. This is one
input to lifecycle investigation, not permission to reload either radio.

Owner-run confirmation on 2026-10-21: `ssh -G wr1200js` parsed the profile,
and `-Check identity` returned the WR1200JS Linux 4.4.198 identity. See
`docs/evidence/WR1200JS-SSH-USER-RUNTIME-2026-10-21.md`. This confirms the
normal Windows PowerShell route only; the managed Codex executor still refuses
SSH before launch.

The helper deliberately exits if Codex's `.sbx-denybin` appears first in the
current `ssh` command resolution and only continues when that normal command
resolves to the standard Windows OpenSSH executable. Do not invoke the system
`ssh.exe` by an absolute path from inside Codex to defeat that check.

For direct Codex execution, the active chat would need a sanctioned permission
profile that allows command networking through the managed proxy and
allowlists only the exact IP `192.168.20.1`; keep the local/private guard on.
The executor must also provide the approved SSH process and credential without
making the private-key file readable to the agent. A network profile's host
allowlist does not limit ports, so the fixed wrapper is what holds the target
port at 22. These conditions are not met by the current managed profile; do not
remove `.sbx-denybin`, disable the sandbox, or broaden access to arbitrary
hosts. The user can inspect the chat's permissions control; if the managed
profile does not offer a scoped exception, its administrator must provide one.

This helper is a convenience for user-run read-only checks. It does not
provision or authorize SSH access for every Codex account, Sol or DeepSeek.
