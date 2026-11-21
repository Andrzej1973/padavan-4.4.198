## Exact byte-string replacement. Default: first occurrence; --count:N or --all.
## Usage: --target:PATH (--old:TEXT | --old-file:PATH)
##        (--new:TEXT | --new-file:PATH) [--count:N | --all]
import std/[os, strutils, parseopt, tempfiles]

proc execute(): string =
  var target, oldText, newText: string
  var hasTarget, hasOld, hasNew, hasMode, replaceAll: bool
  var wanted = 1
  var parser = initOptParser(commandLineParams())
  while true:
    parser.next()
    if parser.kind == cmdEnd: break
    if parser.kind notin {cmdLongOption, cmdShortOption}:
      raise newException(ValueError, "arguments")
    case parser.key
    of "target":
      if hasTarget: raise newException(ValueError, "duplicate")
      target = parser.val
      hasTarget = true
    of "old", "old-file":
      if hasOld: raise newException(ValueError, "duplicate")
      oldText = if parser.key == "old-file": readFile(parser.val) else: parser.val
      hasOld = true
    of "new", "new-file":
      if hasNew: raise newException(ValueError, "duplicate")
      newText = if parser.key == "new-file": readFile(parser.val) else: parser.val
      hasNew = true
    of "count", "all":
      if hasMode: raise newException(ValueError, "duplicate")
      hasMode = true
      if parser.key == "all":
        if parser.val.len != 0: raise newException(ValueError, "arguments")
        replaceAll = true
      else:
        wanted = parseInt(parser.val)
        if wanted <= 0: raise newException(ValueError, "count")
    else:
      raise newException(ValueError, "arguments")
  if not hasTarget or not hasOld or not hasNew or oldText.len == 0:
    raise newException(ValueError, "arguments")
  if not fileExists(target) or symlinkExists(target):
    raise newException(IOError, "target")
  let original = readFile(target)
  if oldText == newText: return "SKIP unchanged exit=0"
  var updated = ""
  var cursor = 0
  var replaced = 0
  while replaceAll or replaced < wanted:
    let at = original.find(oldText, cursor)
    if at < 0: break
    updated.add(original[cursor ..< at])
    updated.add(newText)
    cursor = at + oldText.len
    inc replaced
  if replaced == 0: return "SKIP matches=0 exit=0"
  if not replaceAll and replaced != wanted:
    raise newException(ValueError, "insufficient matches")
  updated.add(original[cursor ..< original.len])
  let destination = absolutePath(target)
  let permissions = getFilePermissions(destination)
  let (temp, tempPath) = createTempFile(".replace-text-", ".tmp", destination.parentDir)
  var closed = false
  defer:
    if not closed: temp.close()
    if fileExists(tempPath): removeFile(tempPath)
  temp.write(updated)
  temp.close()
  closed = true
  setFilePermissions(tempPath, permissions)
  if readFile(destination) != original:
    raise newException(IOError, "target changed")
  moveFile(tempPath, destination)
  return "OK replaced=" & $replaced & " exit=0"

when isMainModule:
  try:
    echo execute()
    quit(0)
  except CatchableError:
    echo "FAIL replacement_not_written exit=1"
    quit(1)
