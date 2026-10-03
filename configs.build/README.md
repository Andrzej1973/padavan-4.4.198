# Router build profiles

Use [Build selected router firmware](https://github.com/Andrzej1973/padavan-4.4.198/actions/workflows/build-multiple-boards.yml)
from the repository's **Actions** page, on branch **main**.

Admission to builds is explicit in [boards.json](../boards.json):

- `wr1200js.config`: active WR1200JS Linux 4.4.198 image-build profile.
  Its full feature configuration is preserved. Device runtime remains pending.
- `mi-mini.config`: reduced Xiaomi Mi Mini profile, full board port pending.
  It is not yet admitted to firmware image builds. Samba/WINS, miniDLNA,
  Transmission and Aria selectors remain documented and disabled.
- `reference/`: original donor configs for comparison; these are not build
  targets and must not be automatically scanned into a build matrix.

A config file alone does not establish board support. Each new board requires
its hardware port, build recipe and image verification before admission.
See [build system](../docs/BUILD-SYSTEM.md).
