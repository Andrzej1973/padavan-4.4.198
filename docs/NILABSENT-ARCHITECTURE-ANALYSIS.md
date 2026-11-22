# Nilabsent architecture comparison

Live reference rechecked on 2026-11-21: [nilabsent/padavan-ng](https://github.com/nilabsent/padavan-ng/tree/c29b12da69b1593a6e8cf65cd43767fc99bb6386),
current `master` still resolves to c29b12da69b1593a6e8cf65cd43767fc99bb6386
(authored 2026-11-01).
Our build donor pin remains d2c5846299949c57a4e867284069900b561dd2a4; reading a
newer upstream revision does not silently update active source.

| Area | Nilabsent source evidence | Adaptation for our4.4 project |
|---|---|---|
| Root | trunk/, toolchain/, uboot/, Dockerfile, docker-compose.yml | Keep our assembly layer and own history; no artificial trunk copy |
| Source | trunk/user, libs, libc, include, vendors, backports, proprietary | Keep package/driver ownership and explicit overlay application |
| Boards | trunk/configs/boards grouped by vendor/bootloader variant | Reuse identity/capability separation; admission remains boards.json |
| Kernel | full trunk/linux-3.4.x with arch/drivers/ralink | Do not transplant3.4 kernel configs or device assumptions to4.4 |
| Toolchain | bundled crosstool-NG; build_toolchain.sh selects sample | Our source pipeline uses GCC10.5,4.4 headers and reviewed libc config |
| Driver sources | proprietary source families, board-selected configuration | Verify exact chips/guards/resources; no generic vendor-capability inference |
| Patches/scripts | component source plus backports and build scripts | Keep explicit ordered transformation anchors and fail on mismatch |
| Documentation | root readmes, change logs, toolchain docs | Our contracts/evidence/handoff required for shared workflow |
| CI/CD | no .github/workflows at inspected revision (API404) | Our Actions queues/checks are our implementation, not attributed upstream |
| Bootloader | uboot retained in upstream | Not imported/rebuilt/changed for this phase |

## Container workflow

At the inspected revision, Compose builds the image from the repository
directory and opens an interactive service. The Dockerfile then clones the
configured upstream branch into /opt/padavan-ng. It does not consume our
working tree, board catalogue or source lock. Copying this container setup
would build a separate checkout. The existing Actions pipeline remains the
build entry point for the WR1200JS overlay and pinned Linux 4.4.198 inputs.

The sample uses GCC7/Linux3.4 and a custom libc source selected by trunk/libc.
Directly copying it would change ABI assumptions. Our source generator already
follows the same bootstrap/configure/ct-ng architecture with the4.4-compatible
profile. [Toolchain source procedure](BUILD-TOOLCHAIN-FROM-SOURCE.md) records pins,
QEMU tests and the boundary between candidate and normal compiler selection.

Local reference snapshots are partial historical donor evidence, not a checkout
of this live revision. A local text scan recorded matching repository paths and
line numbers; its raw path inventory is retained locally, not committed, because
it includes owner-provided and unfinished workspace paths. Raw historical names
and provenance remain untouched. Re-scan live upstream when implementing a later
borrowed feature.
