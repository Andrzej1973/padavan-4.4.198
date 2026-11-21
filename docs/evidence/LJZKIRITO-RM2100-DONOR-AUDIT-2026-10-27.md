# Ljzkirito RM2100 Actions donor audit — 2026-10-27

Source: <https://github.com/Ljzkirito/Actions-Padavan_Redmi-AC2100>,
branch `MeIsReallyBa`, commit `26f8062cf27f26463d47042bc1dbf590bcef4da9`.
The owner archived this repository on 2025-05-06. Its last source commit is
dated 2023-03-10. GitHub reports no repository license. Two files carry
P3TERX MIT notices, but those notices do not grant a blanket license for
everything in the repository. This is a reference audit; no donor code or
configuration was copied into the WR1200JS build.

## Inventory and disposition

| File | What it contains | WR1200JS decision |
| --- | --- | --- |
| `RM2100.config` | MT7621 RM2100 profile, SFE, Chinese language, WINS, most other packages disabled, USB disabled, MT7621 OC value `0x312` | Keep as a board-specific reference only. Our WR1200JS profile already enables SFE and preserves its USB, filesystem, SSH, DNS/VPN, UK/RU language and other requirements. HTOP/MTR remain optional commented selectors by owner decision. Do not copy the RM2100 Product ID, WINS default, disabled services or overclock. |
| `.github/workflows/build-Padavan.yml` | Manual/dispatch build against moving `MeIsReallyBa/padavan-4.4` main; date-named artifact/release, MD5 and SHA256 in release text | Our build already pins source inputs, uses ccache, publishes image artifacts and records SHA256. The useful release-manifest idea belongs after final image and device acceptance: include board, exact source/config revisions and SHA256. Do not adopt its moving source, unpinned third-party actions, workflow-run deletion or automatic release of an unaccepted image. |
| `.github/workflows/update-checker.yml` | Weekly upstream check via a cache key and PAT-triggered build | Do not enable. Its moving upstream and automatic build would add queue/cost and can build an unreviewed source; our checked revisions and failure-only monitor serve different, safer purposes. |
| `diy.sh` | Text substitutions changing LAN and DHCP defaults to `192.168.5.x` | Do not run. WR1200JS addressing is device/user-specific; blind substitutions would risk access. |
| `.gitattributes` | Automatic LF normalization | Already covered more explicitly by our `.gitattributes`. |
| `README.md` | Source attribution and RM2100 notes, including optional IPv6 firewall examples | Retain attribution link. Do not import the suggested IPv6 firewall flush and ACCEPT policy: it would remove protection and is unrelated to WR1200JS requirements. |

The workflow clones `MeIsReallyBa/padavan-4.4` at `main` with depth one and
does not record a fixed source commit in this donor repository. Therefore
this Actions repository is not itself a reproducible firmware source base,
nor does its archived state prove that a particular image or service works
on WR1200JS. The RM2100 profile describes a different board despite the
shared MT7621 SoC. No package, patch or driver source is present here.

## Reusable item for the project backlog

At release time, publish a per-board image manifest with the accepted TRX
SHA256, exact firmware/kernel/driver source revisions, build profile, image
size and acceptance status. The donor's release text demonstrates a simple
checksum listing, while our current CI already calculates image SHA256.
Implement this only after the existing final-image and device gates, with
retention rules that preserve evidence. This audit does not change current
CI, router settings, production configuration or build selection.
