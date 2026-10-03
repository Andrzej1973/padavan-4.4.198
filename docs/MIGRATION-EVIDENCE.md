# Migration evidence — 2026-10-03

- New Public repository: Andrzej1973/padavan-4.4.198.
- Preserved experimental branch SHA: ad5ab44cfc4e021027c9cfbbd1679324e86d929f.
- Its original 206 commits retain their original Git identities.
- History import workflow run 37133865927 completed success.
- Main merge: cc7806d1e718c0e7499a668ed788906d5af25627.
- Local Git diff of configs.build and overlay against the source SHA is empty.
- Local Git fsck passed. A complete Git history bundle was verified.
- Bundle snapshot through main b6d6c656892252a68df992a724ee5b46bfdec2e1:
  586190 bytes, SHA256
  e8e236511415da4dd324bbecdddc6db49a66a5b12fd4e773a06e238ae051a82a.
- This bundle contains project Git history, not all external source archives,
  toolchain assets, release files or a complete standalone build environment.
- Source registry currently covers five direct dependencies; nested package
  dependencies and their owned copies are pending.
- Board catalogue selects WR1200JS and rejects pending Mi Mini for firmware
  builds. Aggregation fixtures cover success, missing image and failed build.
- Workflow YAML and embedded Python parsed locally. Real combined build run
  37134240383 is still in progress; aggregation is not yet CI-proven.

No Linux 4.4 device runtime validation was performed during migration.

