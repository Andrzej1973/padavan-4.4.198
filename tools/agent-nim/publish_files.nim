## Explicit manifest -> structure/checks -> selected files -> commit -> normal push.
## Preview is the default. Never switches branches, resets, force-pushes or reads credentials.
import std/[os, osproc, streams, strutils, parseopt, json, unicode, sets]

proc run(repo, exe: string, args: seq[string]): tuple[code: int, text: string] =
  let process = startProcess(exe, workingDir=repo, args=args,
    options={poUsePath, poStdErrToStdOut})
  defer: process.close()
  process.inputStream.close()
  result.text = process.outputStream.readAll()
  result.code = process.waitForExit()

proc git(repo: string, args: seq[string]): string =
  let resultValue = run(repo, "git", @["--literal-pathspecs"] & args)
  if resultValue.code != 0:
    raise newException(IOError, "git " & args[0] & " failed: " & resultValue.text)
  result = resultValue.text

proc need(condition: bool, message: string) =
  if not condition: raise newException(ValueError, message)

proc pathName(value: string): string =
  result = value.replace('\\', '/')
  need(result.len > 0 and not result.isAbsolute and not result.startsWith("-"), "Unsafe manifest path")
  need(result.find({'\0', '\r', '\n', ':', '*', '?', '[', ']'}) < 0, "Path contains control/pathspec syntax")
  for part in result.split('/'):
    need(part.len > 0 and part notin [".", ".."], "Path must stay inside the repository")
    need(part.toLowerAscii notin [".git", ".ssh", ".aws", ".codex"], "Private/control directory refused")
  need(result != "tools/prepare-wifi-hwnat-mode.py", "Protected unrelated working-tree file refused")

proc structure(repo, path: string) =
  var current = repo
  for part in path.split('/'):
    current = current / part
    need(not symlinkExists(current), "Symlink path refused: " & path)
  need(fileExists(current), "Selected file is missing: " & path)
  let extension = path.splitFile.ext.toLowerAscii
  need(extension notin [".exe", ".dll", ".trx", ".key", ".pem", ".p12", ".pfx",
      ".der", ".crt", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".7z", ".gz",
      ".tgz", ".xz", ".tar", ".bin", ".trx"], "Generated/private binary refused: " & path)
  for part in path.toLowerAscii.split('/'):
    need(part notin [".env", "secrets", "credentials", "authorized_keys"], "Private/control file refused: " & path)
  let data = readFile(current)
  need(data.find('\0') < 0 and validateUtf8(data) == -1, "Expected UTF-8 text: " & path)
  need(not data.startsWith("\xef\xbb\xbf"), "UTF-8 BOM refused: " & path)
  if extension in [".nim", ".py", ".sh", ".yml", ".yaml"]:
    need('\r' notin data, "Use LF line endings: " & path)
  if extension == ".json": discard parseJson(data)

proc main() =
  var manifest, message, bundle: string
  var repo = getCurrentDir()
  var apply, checksOnly: bool
  for kind, key, value in getopt():
    case kind
    of cmdLongOption, cmdShortOption:
      case key
      of "repo": repo = absolutePath(value)
      of "manifest": manifest = value
      of "message": message = value
      of "patch-out": bundle = absolutePath(value)
      of "apply": apply = true
      of "check": checksOnly = true
      of "help", "h":
        echo "publish_files --repo=PATH --manifest=files.json [--check | --apply --message=TEXT [--patch-out=FILE]]"
        return
      else: raise newException(ValueError, "Unknown option: " & key)
    else: need(kind == cmdEnd, "Use named options")
  need(manifest.len > 0 and not (apply and checksOnly), "Manifest required; choose --check or --apply")
  if bundle.len > 0:
    need(apply, "--patch-out requires --apply; bundle is the selected staged patch")
    need(not fileExists(bundle) and not dirExists(bundle) and not symlinkExists(bundle), "Patch output already exists")
    let relative = relativePath(bundle, absolutePath(repo)).replace('\\', '/')
    need(relative.startsWith("../") or relative.isAbsolute, "Write patch outside the checkout")
  let spec = parseFile(manifest)
  let branch = spec["branch"].getStr
  let remote = spec["remote"].getStr
  let expectedRemote = spec["expectedRemote"].getStr
  let executor = spec["executor"].getStr
  need(branch.len > 0 and remote.len > 0 and not remote.startsWith("-"), "Branch/remote required")
  discard git(repo, @["check-ref-format", "refs/heads/" & branch])
  let top = git(repo, @["rev-parse", "--show-toplevel"]).strip.replace('\\', '/')
  let local = absolutePath(repo).replace('\\', '/')
  when defined(windows): need(top.toLowerAscii == local.toLowerAscii, "Use the exact repository root")
  else: need(top == local, "Use the exact repository root")
  need(git(repo, @["branch", "--show-current"]).strip == branch, "Current branch differs; no automatic checkout")
  need(git(repo, @["remote", "get-url", "--push", remote]).strip == expectedRemote, "Push remote URL mismatch")
  need(git(repo, @["diff", "--cached", "--name-only", "-z"]).len == 0, "Existing staged changes: stop and review")
  need(git(repo, @["ls-files", "-u", "-z"]).len == 0, "Unresolved merge conflicts")
  for state in ["MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"]:
    let statePath = git(repo, @["rev-parse", "--git-path", state]).strip
    let full = if statePath.isAbsolute: statePath else: repo / statePath
    need(not fileExists(full) and not dirExists(full), "In-progress Git operation: " & state)
  let role = readFile(repo / "docs/EXECUTION-ROLE.md")
  var owner: string
  for line in role.splitLines:
    if line.startsWith("- **Виконавець:** "):
      owner = line["- **Виконавець:** ".len..^1].split({' ', ',', '('})[0]
      break
  need(executor.len > 0 and owner == executor, "Manifest executor does not own the current role")
  var files: seq[string]
  var selected = initHashSet[string]()
  for entry in spec["files"]:
    let path = pathName(entry.getStr)
    need(path notin selected, "Duplicate manifest file")
    selected.incl(path); files.add(path)
    structure(repo, path)
  need(files.len > 0, "Empty file list")
  echo "Executor: ", executor, "; branch: ", branch, "; remote: ", remote
  for path in files: echo "  selected: ", path
  discard git(repo, @["diff", "--check", "--"] & files)
  need(spec.hasKey("checks") and spec["checks"].len > 0, "At least one explicit check is required")
  for check in spec["checks"]:
    need(check.kind == JArray and check.len > 0, "Check must be an argv array")
    var argv: seq[string]
    for word in check: argv.add word.getStr
    need(argv[0] in ["nim", "python", "python3", "node", "git"], "Use an explicit supported check executable")
    const pyAstCheck = "import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))"
    let validCheck =
      (argv[0] == "nim" and argv.len == 3 and argv[1] == "check" and argv[2] in files and argv[2].endsWith(".nim")) or
      (argv[0] in ["python", "python3"] and argv.len == 4 and argv[1] == "-c" and argv[2] == pyAstCheck) or
      (argv[0] == "node" and argv.len == 3 and argv[1] == "--check" and argv[2] in files) or
      (argv[0] == "git" and argv.len >= 5 and argv[1] == "diff" and argv[2] == "--check" and argv[3] == "--")
    need(validCheck, "Check is outside the restricted validation command forms")
    if argv[0] in ["python", "python3"]:
      need(argv[3] in files and argv[3].endsWith(".py"), "Python AST check must target one selected .py file")
    if argv[0] == "git":
      need(argv[4..^1].len > 0, "Git check must name selected files")
      for checkedPath in argv[4..^1]: need(checkedPath in files, "Git check can only name selected files")
    echo "  check argv: ", $check
    if apply or checksOnly:
      let checked = run(repo, argv[0], argv[1..^1])
      stdout.write checked.text
      need(checked.code == 0, "Check failed; nothing staged")
  for path in files: structure(repo, path)
  if not apply:
    echo "Preview/validation complete. Nothing staged, committed or pushed. Use --apply --message=... to publish."
    return
  need(message.strip.len > 0, "Commit message required")
  need(git(repo, @["diff", "--cached", "--name-only", "-z"]).len == 0, "Checks staged files; stop and review")
  let parent = git(repo, @["rev-parse", "HEAD"]).strip
  discard git(repo, @["fetch", "--no-tags", remote, "refs/heads/" & branch])
  need(git(repo, @["rev-parse", "FETCH_HEAD"]).strip == parent, "Remote and HEAD differ; reconcile explicitly first")
  discard git(repo, @["add", "--"] & files)
  let staged = git(repo, @["diff", "--cached", "--name-only", "-z"])
  need(staged.len > 0, "No selected changes to commit")
  for path in staged.split('\0'):
    if path.len > 0: need(path in selected, "Unexpected staged file; nothing committed")
  discard git(repo, @["diff", "--cached", "--check"])
  if bundle.len > 0:
    writeFile(bundle, git(repo, @["diff", "--cached", "--binary", "--full-index", "--"] & files))
    echo "Combined selected patch: ", bundle
  need(git(repo, @["rev-parse", "HEAD"]).strip == parent, "HEAD changed during preparation")
  stdout.write git(repo, @["commit", "-m", message])
  let commit = git(repo, @["rev-parse", "HEAD"]).strip
  need(git(repo, @["rev-parse", "HEAD^"]).strip == parent, "Unexpected commit parent; push refused")
  for path in git(repo, @["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit]).split('\0'):
    if path.len > 0: need(path in selected, "Commit hook added an unselected file; push refused")
  stdout.write git(repo, @["push", remote, commit & ":refs/heads/" & branch])
  echo "Published commit: ", commit

when isMainModule:
  try: main()
  except CatchableError as error:
    stderr.writeLine("publish_files: " & error.msg & "\nNo automatic rollback: inspect git status before retrying.")
    quit(1)
