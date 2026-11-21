import os, strutils, parseopt

type
  ParserConfig = object
    bufferLen: int
    offset: int
    headerLen: int
    declaredLen: int
    strictCheck: bool

  ParseResult = object
    accepted: bool
    reason: string

proc evaluateIeLength(cfg: ParserConfig): ParseResult =
  if cfg.bufferLen < 0 or cfg.offset < 0 or cfg.headerLen < 0 or cfg.declaredLen < 0:
    return ParseResult(accepted: false, reason: "negative_parameter")

  if not cfg.strictCheck:
    # Режим без суворої перевірки: приймає без звіряння з доступним буфером
    return ParseResult(accepted: true, reason: "unchecked_accepted")

  if cfg.offset > cfg.bufferLen:
    return ParseResult(accepted: false, reason: "offset_exceeds_buffer")

  let remaining = cfg.bufferLen - cfg.offset
  if cfg.headerLen > remaining:
    return ParseResult(accepted: false, reason: "header_exceeds_remaining")

  let afterHeader = remaining - cfg.headerLen
  if cfg.declaredLen == 0:
    return ParseResult(accepted: false, reason: "zero_payload_len")

  if cfg.declaredLen > afterHeader:
    return ParseResult(accepted: false, reason: "payload_exceeds_remaining")

  return ParseResult(accepted: true, reason: "valid")

proc runCase(name: string, cfg: ParserConfig, expectAccepted: bool): bool =
  let res = evaluateIeLength(cfg)
  let ok = (res.accepted == expectAccepted)
  let status = if ok: "PASS" else: "FAIL"
  let mode = if cfg.strictCheck: "strict" else: "unstrict"
  echo status, " | ", name, " | ", mode,
       " | buf=", cfg.bufferLen, " off=", cfg.offset,
       " hdr=", cfg.headerLen, " len=", cfg.declaredLen,
       " | accepted=", res.accepted, " (", res.reason, ")"
  return ok

proc runSuite(): int =
  var failures = 0

  let cases = @[
    ("valid_frame", ParserConfig(bufferLen: 64, offset: 4, headerLen: 2, declaredLen: 16, strictCheck: true), true),
    ("zero_len_rejected", ParserConfig(bufferLen: 64, offset: 4, headerLen: 2, declaredLen: 0, strictCheck: true), false),
    ("truncated_rejected", ParserConfig(bufferLen: 20, offset: 10, headerLen: 2, declaredLen: 12, strictCheck: true), false),
    ("oversized_rejected", ParserConfig(bufferLen: 32, offset: 8, headerLen: 2, declaredLen: 30, strictCheck: true), false),
    ("unstrict_allows_oversized", ParserConfig(bufferLen: 32, offset: 8, headerLen: 2, declaredLen: 30, strictCheck: false), true),
    # Очікуємо FAIL при strictCheck=false, бо неперевірений режим пропустив некоректну довжину
    ("unstrict_catches_missing_check", ParserConfig(bufferLen: 32, offset: 8, headerLen: 2, declaredLen: 30, strictCheck: false), false)
  ]

  for (name, cfg, expected) in cases:
    if not runCase(name, cfg, expected):
      inc failures

  echo "SUMMARY | total=", cases.len, " failures=", failures
  return if failures == 0: 0 else: 1

when isMainModule:
  var cfg = ParserConfig(
    bufferLen: 64,
    offset: 0,
    headerLen: 2,
    declaredLen: 8,
    strictCheck: true
  )
  var customMode = false
  var expectAccepted = true
  var hasExpected = false

  var p = initOptParser(commandLineParams())
  while true:
    p.next()
    case p.kind
    of cmdEnd: break
    of cmdShortOption, cmdLongOption:
      case p.key
      of "b", "buf":
        cfg.bufferLen = parseInt(p.val)
        customMode = true
      of "o", "offset":
        cfg.offset = parseInt(p.val)
        customMode = true
      of "h", "hdr":
        cfg.headerLen = parseInt(p.val)
        customMode = true
      of "l", "len":
        cfg.declaredLen = parseInt(p.val)
        customMode = true
      of "strict":
        cfg.strictCheck = true
        customMode = true
      of "no-strict":
        cfg.strictCheck = false
        customMode = true
      of "expect-accepted":
        expectAccepted = parseBool(p.val)
        hasExpected = true
      else:
        discard
    of cmdArgument:
      discard

  if customMode:
    let targetExpected = if hasExpected: expectAccepted else: cfg.strictCheck
    let ok = runCase("cli_check", cfg, targetExpected)
    quit(if ok: 0 else: 1)
  else:
    quit(runSuite())