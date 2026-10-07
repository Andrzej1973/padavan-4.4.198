#include "settings-snapshot.h"
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
void wr_band_snapshot_release(struct wr_band_settings_snapshot *s)
{
    size_t i;
    if (!s) return;
    if (s->data) {
        volatile char *p = s->data;
        for (i=0;i<s->capacity;++i) p[i]=0;
        free(s->data);
    }
    s->data=0;s->capacity=0;
}
static int valid_dump(const char *data,size_t capacity)
{
    size_t offset=0;
    while (offset<capacity) {
        const char *end=memchr(data+offset,0,capacity-offset);
        const char *eq;
        size_t previous;
        if (!end) return 0;
        if (end==data+offset) {
            /* Empty dump also needs two NUL bytes. Remaining buffer is zero. */
            if (!offset && (capacity<2 || data[1])) return 0;
            for (;offset<capacity;++offset) if (data[offset]) return 0;
            return 1;
        }
        eq=memchr(data+offset,'=',(size_t)(end-data-offset));
        if (!eq || eq==data+offset) return 0;
        for (previous=0;previous<offset;previous+=strlen(data+previous)+1) {
            const char *old_eq=strchr(data+previous,'=');
            size_t length=(size_t)(eq-data-offset);
            if ((size_t)(old_eq-data-previous)==length && !memcmp(data+previous,data+offset,length)) return 0;
        }
        offset=(size_t)(end-data)+1;
    }
    return 0;
}
int wr_band_snapshot_capture(struct wr_band_settings_snapshot *s,size_t capacity,wr_band_snapshot_reader read)
{
    int saved;
    if (!s || s->data || !read || capacity<2 || capacity>(size_t)INT_MAX) { errno=EINVAL;return -1; }
    s->capacity=0;
    s->data=calloc(capacity,1);
    if (!s->data) return -1;
    s->capacity=capacity;
    if (read(s->data,(int)capacity,1)) {
        saved=errno;wr_band_snapshot_release(s);errno=saved;return -1;
    }
    if (!valid_dump(s->data,capacity)) { wr_band_snapshot_release(s);errno=EPROTO;return -1; }
    return 0;
}
const char *wr_band_snapshot_get(const struct wr_band_settings_snapshot *s,const char *key)
{
    size_t offset,length;
    if (!s || !s->data || !key || !*key || strchr(key,'=')) return 0;
    length=strlen(key);
    for (offset=0;offset<s->capacity && s->data[offset];offset+=strlen(s->data+offset)+1) {
        const char *eq=strchr(s->data+offset,'=');
        if ((size_t)(eq-s->data-offset)==length && !memcmp(s->data+offset,key,length)) return eq+1;
    }
    return 0;
}
const char *wr_band_snapshot_wlan_get(const struct wr_band_settings_snapshot *s,int band,const char *name)
{
    char key[64];
    size_t length;
    int written;
    if ((band!=0 && band!=1) || !name || !*name) return 0;
    /* Bounded read: prefix + underscore + name + terminating NUL. */
    for(length=0;length<sizeof(key)-3 && name[length];++length) {}
    if(length>=sizeof(key)-3) return 0;
    if(memchr(name,'=',length)) return 0;
    written=snprintf(key,sizeof(key),"%s_%s",band?"wl":"rt",name);
    if(written<0 || (size_t)written>=sizeof(key)) return 0;
    return wr_band_snapshot_get(s,key);
}
const char *wr_band_snapshot_wlan_key_type(const struct wr_band_settings_snapshot *s,int band)
{
    const char *selected, *key;
    char name[] = "key1";
    long index;
    size_t length;
    if (!s || !s->data || (band!=0 && band!=1)) return 0;
    selected=wr_band_snapshot_wlan_get(s,band,"key");
    /* The original generator defaults an absent/out-of-range selector to 1.
     * strtol also preserves its accepted leading whitespace/sign/number text,
     * while avoiding undefined integer conversion on an oversized selector. */
    index=selected?strtol(selected,0,10):1;
    if(index<1 || index>4) index=1;
    name[3]=(char)('0'+index);
    key=wr_band_snapshot_wlan_get(s,band,name);
    length=key?strlen(key):0;
    if(length==5 || length==13) return "1";
    if(length==10 || length==26) return "0";
    return wr_band_snapshot_wlan_get(s,band,"key_type");
}
