#include <assert.h>
#include "handshake-observation.h"
#include "handshake-cache.h"
static int parse(const char *s,struct wr_handshake_observation *out){
 FILE *fp=tmpfile();int ok;assert(fp);assert(fputs(s,fp)>=0);rewind(fp);
 ok=wr_handshake_read(fp,1000,300,out);assert(!fclose(fp));return ok;
}
#define KEY "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
int main(void){
 struct wr_handshake_observation o,unchanged;
 assert(parse("",&o)&&o.peers==0);
 assert(parse(KEY "\t0\n",&o)&&o.peers==1&&o.never==1&&!o.has_age);
 assert(parse(KEY "\t950\n",&o)&&o.recent==1&&o.youngest_age==50);
 assert(parse(KEY "\t699\n",&o)&&o.old==1);
 assert(parse(KEY "\t1001\n",&o)&&o.future==1&&!o.has_age);
 memset(&o,0x55,sizeof(o));unchanged=o;
 assert(!parse(KEY "\t950\n" KEY "\t951\n",&o));assert(!memcmp(&o,&unchanged,sizeof(o)));
 assert(!parse(KEY "\t18446744073709551616\n",&o));
 assert(!parse(KEY "\t-1\n",&o));assert(!parse(KEY "\t950",&o));
 assert(!parse("invalid\t950\n",&o));assert(!parse(KEY "\t950 extra\n",&o));
 {FILE *fp=tmpfile();unsigned i;assert(fp);
  for(i=0;i<WR_HANDSHAKE_PEERS+1;i++)fprintf(fp,"%043u=\t950\n",i);
  rewind(fp);assert(!wr_handshake_read(fp,1000,300,&o));assert(!fclose(fp));}
 {struct wr_handshake_cache c={0};uint64_t age;
  assert(wr_handshake_cache_get(&c,10,30,&age)==WR_HS_UNKNOWN);
  assert(parse(KEY "\t950\n",&o));
  wr_handshake_cache_publish(&c,10,1,&o);
  assert(wr_handshake_cache_get(&c,40,30,&age)==WR_HS_CURRENT&&age==30);
  assert(wr_handshake_cache_get(&c,41,30,&age)==WR_HS_STALE);
  wr_handshake_cache_publish(&c,20,0,NULL);
  assert(wr_handshake_cache_get(&c,21,30,&age)==WR_HS_STALE&&c.observation.recent==1);
  assert(wr_handshake_cache_get(&c,9,30,&age)==WR_HS_UNKNOWN);
  wr_handshake_cache_publish(&c,5,0,NULL);assert(!c.has_sample);
  wr_handshake_cache_publish(&c,6,1,&o);assert(wr_handshake_cache_get(&c,6,30,&age)==WR_HS_CURRENT);}
 puts("PASS bounded handshake observations; peer keys not emitted, connectivity not inferred");return 0;
}
