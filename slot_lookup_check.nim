type
  SlotEntry = object
    wcid: int
    mac: string
    ifIdx: int
    active: bool
    assocGen: uint32

  LookupResult = object
    found: bool
    wcid: int
    reason: string

proc lookupSlot(table: seq[SlotEntry], mac: string, reqIfIdx: int, reqGen: uint32, macOnly: bool): LookupResult =
  for e in table:
    if e.mac == mac:
      if macOnly:
        return LookupResult(found: true, wcid: e.wcid, reason: "matched_mac_only")
      if not e.active:
        continue
      if e.ifIdx != reqIfIdx:
        continue
      if reqGen != 0'u32 and e.assocGen != reqGen:
        continue
      return LookupResult(found: true, wcid: e.wcid, reason: "matched_strict")
  return LookupResult(found: false, wcid: -1, reason: "not_found")

when isMainModule:
  let table = @[
    SlotEntry(wcid: 3, mac: "AA:BB:CC:DD:EE:01", ifIdx: 0, active: false, assocGen: 1),
    SlotEntry(wcid: 7, mac: "AA:BB:CC:DD:EE:01", ifIdx: 2, active: true,  assocGen: 2)
  ]

  let r1 = lookupSlot(table, "AA:BB:CC:DD:EE:01", reqIfIdx = 2, reqGen = 2, macOnly = true)
  echo "TEST 1 (mac_only_legacy) | wcid=", r1.wcid, " | expected=7 | PASS=", (r1.wcid == 7)

  let r2 = lookupSlot(table, "AA:BB:CC:DD:EE:01", reqIfIdx = 2, reqGen = 2, macOnly = false)
  echo "TEST 2 (strict_context)  | wcid=", r2.wcid, " | expected=7 | PASS=", (r2.wcid == 7)

  let r3 = lookupSlot(table, "AA:BB:CC:DD:EE:01", reqIfIdx = 2, reqGen = 99, macOnly = false)
  echo "TEST 3 (stale_gen_drop)  | found=", r3.found, " | expected=false | PASS=", (not r3.found)