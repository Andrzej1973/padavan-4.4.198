"""Require a strong selector in paired runtime sources; baseline stays untouched."""
WEAK='''__attribute__((weak)) int wr_iot_generation_profile_request(struct wr_iot_precreated_profile_request *out)
{ (void)out; return 0; }'''
def bind(text):
 if text.count('#include "wr-iot/generation-profile.h"')!=1 or text.count(WEAK)!=1:
  raise ValueError('Exact prepared generation selector fallback required')
 return text.replace(WEAK,'/* Paired runtime requires the strong saved-config-store selector. */',1)
