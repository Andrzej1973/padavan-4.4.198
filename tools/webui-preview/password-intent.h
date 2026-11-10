/* Explicit Modern WPA-Personal intent planning only. No NVRAM writes or logging.
 * Not wired to CGI until the complete request adapter is verified. */
#ifndef WR_MODERN_PASSWORD_INTENT_H
#define WR_MODERN_PASSWORD_INTENT_H
#include "validate.h"

typedef const char *(*wr_modern_secret_read)(void *, const char *);
struct wr_modern_password_plan {
 int keep;
 char value[65]; /* Owned snapshot; never returned to the browser. */
};
static void wr_modern_password_clear(struct wr_modern_password_plan *plan)
{
 volatile unsigned char *cursor;
 size_t i;
 if (!plan) return;
 cursor = (volatile unsigned char *)plan;
 for (i = 0; i < sizeof(*plan); i++) cursor[i] = 0;
}
static enum wr_shared_wifi_result wr_modern_password_prepare(
 struct wr_modern_password_plan *out, const char *intent, const char *band,
 const struct wr_shared_wifi_fields *request, wr_modern_secret_read read_secret,
 void *context)
{
 struct wr_shared_wifi_fields fields;
 struct wr_modern_password_plan next;
 enum wr_shared_wifi_result result;
 const char *value;
 int keep;
 if (!out || !intent || !band || !request) return WR_SHARED_WIFI_MISSING;
 if (strcmp(band,"rt") && strcmp(band,"wl")) return WR_SHARED_WIFI_SECURITY;
 if (!strcmp(intent,"keep")) keep=1;
 else if (!strcmp(intent,"change")) keep=0;
 else return WR_SHARED_WIFI_SECURITY;
 if (!request->auth || strcmp(request->auth,"psk")) return WR_SHARED_WIFI_SECURITY;
 /* Keep intent must omit the posted PSK entirely, including empty strings. */
 if (keep && request->password) return WR_SHARED_WIFI_SECURITY;
 fields=*request;
 /* Validate non-secret fields before retrieving the stored secret. */
 fields.password="validation-only";
 result=wr_shared_wifi_validate(&fields);
 if (result!=WR_SHARED_WIFI_OK) return result;
 if (keep) {
  if (!read_secret) return WR_SHARED_WIFI_MISSING;
  value=read_secret(context,!strcmp(band,"rt")?"rt_wpa_psk":"wl_wpa_psk");
 } else value=request->password;
 fields.password=value;
 result=wr_shared_wifi_validate(&fields);
 if (result!=WR_SHARED_WIFI_OK) return result;
 memset(&next,0,sizeof(next));next.keep=keep;
 memcpy(next.value,value,strlen(value)+1);
 *out=next;
 wr_modern_password_clear(&next);
 return WR_SHARED_WIFI_OK;
}
#endif
