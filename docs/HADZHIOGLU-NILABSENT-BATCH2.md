# Hadzhioglu → nilabsent — Batch 2

## HTTPD variables

`trunk/user/httpd/variables.c` exists in both trees. nilabsent adds the WireGuard-specific variable `vpns_public_x` under `APP_WIREGUARD`; Hadzhioglu does not contain this symbol.

Decision: **🔵 keep nilabsent**. This is newer nilabsent functionality, not a missing Hadzhioglu feature.

## RC Makefile

`trunk/user/rc/Makefile` exists in both. nilabsent adds:

- `vpn_wireguard.o` when WireGuard or AmneziaWG is enabled;
- `-fvisibility=hidden`;
- extra romfs command links including `ntpc_syncnow`, `restart_zapret`, and `update_resolvconf`;
- newer Samba condition handling with `APP_SMBD36`.

Decision: **🔴 do not replace nilabsent's Makefile with Hadzhioglu's**.

## vpn_wireguard.c

`trunk/user/rc/vpn_wireguard.c` exists in nilabsent and is not present in the searched Hadzhioglu tree. It controls WireGuard server/client start, stop, restart, reload, update and watchdog through `/usr/bin/wgs.sh` and `/usr/bin/wgc.sh`.

Decision: **🔵 keep nilabsent**.

## AmneziaWG

nilabsent contains a dedicated kernel implementation under `trunk/linux-3.4.x/net/amneziawg/`, together with Kconfig/Kbuild/Makefile integration and firmware configuration. The searched Hadzhioglu tree does not contain this feature.

Decision: **🔵 keep nilabsent**. It is a newer feature and must not be treated as something to restore from Hadzhioglu.

## KMS

Searches for `kms` in nilabsent primarily hit Linux DRM Kernel Mode Setting. This is unrelated to a Windows KMS server. Searches of the Hadzhioglu source did not find `vlmcsd` or a Windows KMS implementation.

Decision: **do not copy anything for KMS yet**. If the KMS server was present in a specific prebuilt Hadzhioglu-based firmware, we need that exact source/package before transplanting it.

## Important conclusion

So far, the comparison is showing that nilabsent is not simply a stripped Hadzhioglu tree. It has substantial newer functionality (WireGuard/AmneziaWG, newer rc integration, extra services). Therefore the safe direction is **selective backporting from Hadzhioglu into nilabsent**, not replacing nilabsent files wholesale.
