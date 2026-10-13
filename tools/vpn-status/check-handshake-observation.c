#include <assert.h>
#include "handshake-observation.h"
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
 puts("PASS bounded handshake observations; peer keys not emitted, connectivity not inferred");return 0;
}
