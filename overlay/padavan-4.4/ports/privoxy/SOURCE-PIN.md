# Privoxy 4.2 source pin

Source URL: https://www.privoxy.org/sf-download-mirror/Sources/4.2.0%20%28stable%29/privoxy-4.2.0-stable-src.tar.gz

Fallback official distribution: https://downloads.sourceforge.net/project/ijbswa/Sources/4.2.0%20%28stable%29/privoxy-4.2.0-stable-src.tar.gz

Archive SHA256: 6f91267f81f626c416994db89ab62f4d09246eebf4754b81186e13a18ee9028f

Archive size: 1791064 bytes.

Checksum corroboration: https://github.com/freebsd/freebsd-ports/blob/main/www/privoxy/distinfo (checked 2026-10-02). A fetched archive must still be checked against this hash before extraction; no local archive has been downloaded yet.

Extracted directory: privoxy-4.2.0-stable.

Build requirement found in 4.2 configure.in: linker appends BOTH -lpcre2-8 and -lpcre2-posix. Therefore runtime packaging must retain both shared libraries and their symlinks unless a verified build proves static linkage. The initial PCRE2 candidate ROMFS recipe omitted POSIX; corrected before integration.

Do not inherit FreeBSD defaults wholesale: they enable HTTPS inspection, which is not authorized as a router default. Preserve existing router configuration and default service OFF. Pin GPL license files from the source package alongside the final preserved source assets.

Compile proof and complete package/lifecycle/WebUI integration are outstanding.
