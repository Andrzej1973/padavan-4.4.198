# Build 151: RSSI query candidate compilation

[Build 151](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38048663806) completed successfully. Its log confirms the real-kernel handler probe compiled, the administrator-only RSSI query was prepared in the isolated driver tree, and both complete modules linked afterwards. Downloaded module bytes match the recorded SHA-256:

- `mt76x2_ap.ko`: `948d57a8199965bf8a1a833cde64f0b9cc85e5c279a2caa34656660ef4d6f1a9`.
- `mt76x3_ap.ko`: `936547d7bcffa3a133625ec69ff925967ce4eb6d4c2c405bc0898d721bcebd27`.

[ABI 310](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38048663776) completed successfully. Source preparation checks cover both query dispatches, radio mapping, header closure and rejection of repeat preparation or second-radio conflicts without partial writes.

This establishes compilation in the actual isolated driver configurations. It does not execute ioctl on a router, exercise allocation/user-copy faults or prove adapter restart behavior. These candidate modules are not installed in the normal TRX. Userspace response decoding, collection, WebUI integration and runtime verification remain required.
