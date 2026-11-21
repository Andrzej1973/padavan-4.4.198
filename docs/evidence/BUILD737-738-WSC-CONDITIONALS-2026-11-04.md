# Optional 737/738: WSC conditional compilation

Both optional 41841361021 (efbf784b) and 41841385552 (b4117cd6) failed
in full WSC compilation on six -Werror=misleading-indentation errors:
wsc.c 3658/3668/3829/4755/8002 and crypt_biginteger.c 3502. Original jobs
126613592084/126625412504 agree. APCLI declaration failure is resolved.
Monitor 41848368626 artifact 13331708517 identifies correct step but old
default prefix parser omits cause. Existing branch suffix parser passes added
exact-error regression; no default branch mutation or duplicate parser fix.
Feature preparer adds braces only to reviewed single-statement conditions.
Non-brace/non-whitespace token streams unchanged. All three modified source
hashes recorded; pinned-input preparation, drift rejection, provenance and
Nim monitor offline tests pass. Full target WSC remains pending rerun.
Independent artifact 13331818228 verification: b4117cd6 baseline MIPS module
5574520 bytes SHA256 6a1d9454d4ba1858651e4a4f5d9fa3dfbf2da323c4c90dd9883600908f6f50a2.
Manifest confirms ROM-timeout layer output e163022369932a6306c4076a2d86e67564d4fb91a31bfa03761ec846bf8df9d7,
epoch_verified=false. Not a reload epoch, firmware shutdown or runtime proof.
Scratch fixtures/compiler cache removed; remote artifacts read in memory,
no archive retained. Preserved owner references/unfinished inputs. Router untouched.
