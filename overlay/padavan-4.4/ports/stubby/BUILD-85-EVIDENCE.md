# Stubby cross-compilation evidence — build 85

Run: https://github.com/Andrzej1973/youhua-wr1200js-nilab/actions/runs/37101483808
Job: 111141721943. Head: 76a2c14ed9c028ed8e1f74abd32727454ae28e3e.
Verified 2026-10-03 through jobs API and decoded job log. Job conclusion: success.

The standalone Stubby candidate step completed successfully between
06:19:23 and 06:19:42 UTC. The log confirms static getdns libraries built,
bundled Stubby sources compiled, and the final executable linked:
`[100%] Built target stubby`.

The executed script checks both source archive SHA256 values and verifies
the executable's ELF Machine is MIPS before completing. The compiled binary
is bundled in the diagnostic artifact; it is not installed in this firmware.

Artifact: https://github.com/Andrzej1973/youhua-wr1200js-nilab/actions/runs/37101483808/artifacts/11266733205
Archive size: 301216 bytes. This is the compressed artifact size, not the
binary's size or contribution to the firmware image.

OpenSSL deprecated SHA512 API warnings and a signedness warning in Stubby
are present; they did not fail compilation. Source modernization may be
considered separately without suppressing warnings or claiming runtime proof.

Not established: full package recipe compilation, rc/httpd integration,
ROMFS dependency closure, live configuration migration, DNS-over-TLS queries,
certificate validation, lifecycle behavior or router runtime support.
