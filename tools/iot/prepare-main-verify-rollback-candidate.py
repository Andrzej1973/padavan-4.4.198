#!/usr/bin/env python3
"""Stage synchronous checked rollback for a failed main VERIFY, nonproduction."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prior-manifest", type=Path,
                        help="Reviewed pre-VERIFY composition manifest (all hashes checked)")
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    prior = (args.prior_manifest.resolve(strict=True) if args.prior_manifest else
             source.parent / "mt7603-main-recovery-steering-race-v19-20261028-composition.json")
    v20 = Path(str(source) + ".manifest.json")
    base = json.loads(prior.read_text(encoding="utf-8"))
    verify = json.loads(v20.read_text(encoding="utf-8"))
    if (base.get("production_installed") is not False or
            verify.get("production_installed") is not False or
            verify.get("main_readiness_verify_bound") is not True or
            verify.get("recovery_owner_bound") is not False):
        parser.error("expected isolated, unbound v20 VERIFY candidate")
    records = {row["path"]: row for row in base["files"]}
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if len(records) != len(base["files"]) or files != set(records):
        parser.error("source file set differs from reviewed composition")
    changed = "os/linux/rt_main_dev.c"
    for name, row in records.items():
        expected = verify["rt_main_dev_sha256"] if name == changed else row["sha256"]
        if sha(source / name) != expected:
            parser.error("source hash mismatch: " + name)
    data = (source / changed).read_text(encoding="utf-8")
    old = ''' if (IS_MT7603(adapter)&&
     !wr_iot_main_readiness_verify(adapter,net_dev,generation)) {
  /* VERIFY failure leaves main_ready false and retains this acquired owner.
   * No secondary BSS may open; a recovery owner is still required before
   * this candidate can be bound to production or PCI removal. */
  DBGPRINT(RT_DEBUG_ERROR,
   ("MT7603 main radio readiness unverified; keeping secondary BSS closed\\n"));
  return -1;
 }'''
    new = ''' if (IS_MT7603(adapter)&&
     !wr_iot_main_readiness_verify(adapter,net_dev,generation)) {
  struct wr_iot_radio_ticket close_ticket;
  unsigned long close_generation=0,close_token=0,wait_serial=0;
  int closed=0;
  /* ndo_open owns RTNL here. A failed VERIFY has retained the exact main
   * reference; attempt checked close before returning an open failure. */
  if (wr_iot_main_close_begin_checked(adapter,net_dev,&close_ticket,
        &close_generation,&close_token,&wait_serial)==0 &&
      close_generation==generation &&
      wr_iot_main_close_preclose_once(adapter,net_dev,close_generation,
                                     &close_ticket)==0 &&
      wr_iot_main_close_continue_checked(adapter,net_dev,close_generation,
                                         close_token,&close_ticket)==0)
   closed=1;
  if (closed)
   RT_MOD_DEC_USE_COUNT();
  else
   DBGPRINT(RT_DEBUG_ERROR,
    ("MT7603 main VERIFY failed; checked close incomplete, retaining owner\\n"));
  return -1;
 }'''
    if data.count(old) != 1:
        parser.error("main VERIFY failure branch differs from reviewed v20")
    if any(data.count(name) < 2 for name in (
            "wr_iot_main_close_begin_checked(",
            "wr_iot_main_close_preclose_once(",
            "wr_iot_main_close_continue_checked(")):
        parser.error("checked close family is absent")
    shutil.copytree(source, output)
    (output / changed).write_text(data.replace(old, new, 1), encoding="utf-8", newline="\n")
    records[changed]["sha256"] = sha(output / changed)
    records[changed]["stage"] += "+main-verify-checked-rollback"
    base["main_readiness_verify_bound"] = True
    base["main_verify_checked_rollback_staged"] = True
    base["main_close_recovery_bound"] = False
    base["pci_release_gate_bound"] = False
    base["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(base, indent=2) + "\n", encoding="utf-8")
    verify["rt_main_dev_sha256"] = records[changed]["sha256"]
    verify["main_verify_checked_rollback_staged"] = True
    Path(str(output) + ".manifest.json").write_text(
        json.dumps(verify, indent=2) + "\n", encoding="utf-8")
    print("PASS staged checked main VERIFY rollback; incomplete close still retains owner")


if __name__ == "__main__":
    main()
