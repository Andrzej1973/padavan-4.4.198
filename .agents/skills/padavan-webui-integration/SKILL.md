---
name: padavan-webui-integration
description: Implement or review a production Padavan WebUI form or page in this repository when it touches ASP/CGI, NVRAM, services, or board capabilities. Do not use for a standalone visual mockup.
---

# Padavan WebUI integration

Read `AGENTS.md` and the current project handoff before changing this repository. Identify the exact board, branch, dirty files and affected Classic or Modern page. Keep Classic behavior unless the task explicitly changes it.

1. Trace each visible control through its actual form name, client validation, ASP/CGI or HTTP handler, NVRAM key, apply script, service and final image. Use existing save/apply paths; do not create a parallel persistence mechanism.
2. Check the effective board configuration and capability evidence. For unsupported features, verify both the UI and backend policy; a visual hide alone is insufficient. Start with `tools/wifi-capabilities/boards/` and `tools/board-capabilities/` where applicable, then check source and the built ROMFS. Treat unknown capabilities as unverified.
3. Preserve band-specific values, localization, keyboard access and mobile layout. Escaping and validation must cover values returned from NVRAM and services. A tab change must not save or reset settings.
4. For networking changes, trace WAN/LAN, bridge, firewall, DNS/DHCP, VPN and hardware offload paths affected by the control. Check IPv4 and IPv6 when enabled. A UI switch does not prove a service or isolation works.
5. Run only targeted checks needed for the change. Report source checks, local preview, final ROMFS/image and router runtime as separate evidence levels. The demo at `tools/webui-preview/` does not prove production behavior.

Use relevant user or plugin Skills for Neon design, router profiles, network audit, browser testing, regression review and Git when available. Do not copy their generic instructions into this repository. If one is unavailable to another account, the repository files above remain the source of project requirements.
