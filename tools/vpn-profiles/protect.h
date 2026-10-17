#ifndef WR_VPN_PROTECT_H
#define WR_VPN_PROTECT_H

#include <stddef.h>
#include <string.h>

/* Split a comma-separated protected-prefix list into NUL-terminated tokens.
 * Spaces and tabs around a token are trimmed. Empty tokens and lists longer
 * than the caller's capacity are rejected: a typo in `wrvpn_protect` must
 * fail the start instead of silently dropping a LAN/management prefix. */
static inline int wr_vpn_parse_protect(const char *text, char *buffer,
                                       size_t capacity, const char **out,
                                       size_t maximum)
{
    size_t count = 0, used = 0;
    while (text && *text) {
        const char *comma = strchr(text, ',');
        const char *token = text;
        const char *end = comma ? comma : text + strlen(text);
        size_t length = (size_t)(end - token);
        while (length && (*token == ' ' || *token == '\t')) { token++; length--; }
        while (length && (end[-1] == ' ' || end[-1] == '\t')) { end--; length--; }
        if (!length || used + length + 1 > capacity || count >= maximum) return -1;
        memcpy(buffer + used, token, length);
        buffer[used + length] = 0;
        out[count++] = buffer + used;
        used += length + 1;
        text = comma ? comma + 1 : NULL;
    }
    return (int)count;
}

#endif
