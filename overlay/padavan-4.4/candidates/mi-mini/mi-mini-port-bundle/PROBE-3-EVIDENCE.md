# MT7620 radio object compile evidence

GitHub run37125017942, job111208437809, success at commit
917efb57283bd3f12661fc878307ac2b56721655, observed2026-10-03.
Artifact11275180409: compile log, effective kernel config, ELF header and
toolchain archive checksum. Artifact is diagnostics, not a firmware image.

Source reconstruction, Kconfig-selected SOC_MT7620/MI_MINI_RADIO/WDS/MBSS/APCLI
checks and kernel prepare passed. Log includes compilation of RT6352, RF and
LOFT calibration and link of rt2860v2_ap.o and its built-in.o. Workflow checks
the composite object's MIPS ELF header. This is real driver object compilation,
not merely a successful file-copy step.

Full vmlinux link and symbol resolution remain unverified. No complete Mi Mini
DTS/firmware, boot, Wi-Fi, Ethernet or recovery verification. Common radio
feature selection and 5GHz control-plane integration still pending.

Warnings include undefined CONFIG_RALINK_RAM_SIZE selecting a legacy low-memory
branch and inherited source indentation warnings. Inspect these before accepting
runtime behavior; a green object build alone does not validate selected logic.
Parallel WR1200JS build104/run37125017937 completed success separately.
