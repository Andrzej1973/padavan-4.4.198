# Band Steering profile compatibility candidate

Read-only profile-policy.c validates an explicit enable request against both main-network configurations. Disabled requests do not inspect or modify credentials. Enable requires both radios, equal nonempty SSIDs (maximum 32 bytes), equal visibility, and compatible equal security. Supported candidate modes are open without WEP or matching WPA Personal modes 0/1/2 with matching cipher and PSK. Enterprise/WEP are refused without changing existing settings. PSKs accept 8–63 printable ASCII bytes or 64 hexadecimal characters. Invalid fields return reason codes without logging credentials.

This module is not yet connected to rc, the daemon or WebUI; presence alone does not enforce runtime configuration. Integration must copy NVRAM values into stable bounded storage, prevent settings changes from racing activation, and preserve independent band/guest settings. Profiles must include only the main BSS in steering and service activation must be exclusive. Factory enable remains off.

The separate legacy guest-isolation source fixtures passed host sanitizers and MIPS compilation in run 37192562591 after fixing mock-variable shadowing. Full guest-patched driver compilation and router runtime remain pending. Profile policy CI is newly requested; YAML parsing alone is not a C compile result.
