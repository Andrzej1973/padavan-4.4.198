/* Pure radio request validation. Policy mask must come from a trusted server-side
 * effective-policy provider; never from posted data. No provider is bound yet. */
#ifndef WR_MODERN_RADIO24_VALIDATE_H
#define WR_MODERN_RADIO24_VALIDATE_H
#include <string.h>
struct wr_modern_radio24_request {
 const char *radio,*hidden,*mode,*width,*extension,*channel;
};
struct wr_modern_radio24_policy {unsigned int channels;int verified;unsigned int ht40_primary;};
enum wr_modern_radio24_result {WR_RADIO24_OK,WR_RADIO24_MISSING,WR_RADIO24_INVALID,WR_RADIO24_POLICY_UNAVAILABLE};
static enum wr_modern_radio24_result wr_modern_radio24_validate(
 const struct wr_modern_radio24_request *r,const struct wr_modern_radio24_policy *p)
{
 unsigned int channel;int ht,secondary;
 if(!r||!p)return WR_RADIO24_MISSING;
 if(!p->verified || !p->channels || (p->channels & ~0x3ffeU) ||
    (p->ht40_primary & ~p->channels))return WR_RADIO24_POLICY_UNAVAILABLE;
 if(!r->radio||!r->hidden||!r->mode||!r->channel)return WR_RADIO24_MISSING;
 if((strcmp(r->radio,"0")&&strcmp(r->radio,"1")) ||
    (strcmp(r->hidden,"0")&&strcmp(r->hidden,"1")))return WR_RADIO24_INVALID;
 if(strlen(r->mode)!=1 || r->mode[0]<'0' || r->mode[0]>'5')return WR_RADIO24_INVALID;
 if(!strcmp(r->channel,"0"))channel=0;
 else if(strlen(r->channel)==1 && r->channel[0]>='1' && r->channel[0]<='9')channel=(unsigned int)(r->channel[0]-'0');
 else if(strlen(r->channel)==2 && r->channel[0]=='1' && r->channel[1]>='0' && r->channel[1]<='3')channel=10U+(unsigned int)(r->channel[1]-'0');
 else return WR_RADIO24_INVALID;
 if(channel && !(p->channels & (1U<<channel)))return WR_RADIO24_INVALID;
 ht=!strcmp(r->mode,"2")||!strcmp(r->mode,"3")||!strcmp(r->mode,"5");
 /* Inapplicable HT fields must be omitted, not silently changed or persisted. */
 if(!ht)return (!r->width&&!r->extension)?WR_RADIO24_OK:WR_RADIO24_INVALID;
 if(!r->width)return WR_RADIO24_MISSING;
 if(!strcmp(r->width,"0"))return r->extension?WR_RADIO24_INVALID:WR_RADIO24_OK;
 if(strcmp(r->width,"1") || !r->extension ||
    (strcmp(r->extension,"0")&&strcmp(r->extension,"1")))return WR_RADIO24_INVALID;
 if(!p->ht40_primary)return WR_RADIO24_POLICY_UNAVAILABLE;
 if(!channel)return WR_RADIO24_OK; /* Driver auto-selection/coexistence still authoritative. */
 if(!(p->ht40_primary & (1U<<channel)))return WR_RADIO24_INVALID;
 secondary=(int)channel+(!strcmp(r->extension,"1")?4:-4);
 if(secondary<1 || secondary>13 || !(p->channels & (1U<<(unsigned int)secondary)))return WR_RADIO24_INVALID;
 return WR_RADIO24_OK;
}
#endif
