# WR1200JS build #540: effective beacon-lock units

- Workflow: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40016197462
- Final workflow result: success. The WR1200JS build, downloads index, and
  firmware ZIP jobs all completed successfully; this is CI/image evidence.
- Branch commit: `160a1bc4b37cd3e47754e3681a2ecce97d7e6c45`.
- Pinned driver source: `c25283e915a2a00a763774dd255b14aff997285e`.
- Artifact: `wr1200js-iot-radio-capacity/mt76x3.json`, downloaded under
  `artifacts-540/wr1200js-iot-radio-capacity/`.
- Artifact SHA256: `8972ae0c6cb9534b40aaf18a7e93a9a1f983c7b072d0166c9d6dc67fcc6fc7f4`.

The target Kbuild probe completed with a source/config limit of 16 BSS and
`all_unit_flags_available=true`, `all_site_activity_available=true`. Each
of the four inspected source units has effective
`MULTI_CORE_SUPPORT=false`:

| Unit | Source lock owner | Form | Survives target directives |
| --- | --- | --- | --- |
| `ap/ap_cfg.c` | `Set_BcnStateCtrl_Proc` | SEM | yes |
| `ap/ap_nps.c` | `RT28xx_UpdateTimToAsic` | SEM | yes |
| `common/cmm_data_pci.c` | `RTMPHandleBcnDmaDoneInterrupt` | SEM | yes |
| `common/cmm_mac_pci.c` | `RTMPFreeTxRxRingMemory` | SEM | no |
| `common/cmm_mac_pci.c` | `RTMPRingCleanUp` | IRQ | yes |
| `common/cmm_mac_pci.c` | `PDMAResetAndRecovery` | IRQ | yes |
| `common/cmm_mac_pci.c` | `RT28xx_UpdateBeaconToAsic` | SEM | yes |

In the pinned Linux wrapper, when `MULTI_CORE_SUPPORT` is absent the SEM
and IRQ forms both use the BH spin-lock wrapper; with that macro present
the IRQ form instead masks interrupts. This result resolves the effective
macro branch for these four baseline units. Directive survival alone does
not establish that a call is reachable on WR1200JS or that no hard-IRQ
callback can acquire the same lock.

The separate partial IoT candidate has 19 source-text lock sites in eight
units, and this artifact is from the unmodified pinned driver. It does not
prove candidate-wide lock consistency, adapter lifetime, DMA/TxS drain,
radio behavior, or a safe production IoT BSS. Its `runtime_verified` is
false. The candidate needs a complete generated-tree audit and target
compilation before the beacon admission gate can be accepted. No router
state was changed while collecting this evidence.

The inspected `iot-unified-txs-handler-snapshot-v2-20261023/manifest.json`
explicitly records `complete_driver_tree=false`, `target_compiled=false`, and
`beacon_lock_forms_complete_tree=false`. It omits the unchanged `ap/ap_nps.c`
owner. The next candidate check must assemble the pinned full MT7603 tree,
overlay only the candidate's changed files, and inventory every compiled
`BcnRingLock` owner using the target Kbuild flags. Until that check exists,
the baseline six surviving sites cannot be extrapolated to the candidate.
