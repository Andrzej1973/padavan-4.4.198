/* Bounded, read-only sysfs inventory. No bind/unbind or shell commands. */
#ifndef WR_USBIP_SYSFS
#define WR_USBIP_SYSFS "/sys/bus/usb/devices"
#endif
static int wr_usbip_busid(const char *s)
{
 const char *p = s;
 if (!s || strlen(s) > 31 || !isdigit((unsigned char)*p)) return 0;
 while (isdigit((unsigned char)*p)) p++;
 if (*p++ != '-' || !isdigit((unsigned char)*p)) return 0;
 for (;;) {
  while (isdigit((unsigned char)*p)) p++;
  if (!*p) return 1;
  if (*p++ != '.' || !isdigit((unsigned char)*p)) return 0;
 }
}
static void wr_usbip_hex(const char *id, const char *attribute, char *out, size_t digits)
{
 char path[256], value[16];
 FILE *fp;
 size_t i;
 out[0] = 0;
 snprintf(path, sizeof(path), "%s/%s/%s", WR_USBIP_SYSFS, id, attribute);
 fp = fopen(path, "r");
 if (!fp) return;
 if (!fgets(value, sizeof(value), fp)) { fclose(fp); return; }
 fclose(fp);
 if (strlen(value) != digits && !(strlen(value) == digits+1 && value[digits]=='\n')) return;
 for (i=0; i<digits; i++) if (!isxdigit((unsigned char)value[i])) return;
 memcpy(out, value, digits); out[digits] = 0;
}
/* Exact serial bytes encoded for JSON; private identity data, not a public log.
 * Empty means unavailable/invalid, never permission to restore an export. */
static void wr_usbip_serial_hex(const char *id, char out[513])
{
 char path[256];
 unsigned char bytes[258];
 const char *hex="0123456789abcdef";
 FILE *fp;
 size_t n,i;
 out[0]=0;
 snprintf(path,sizeof(path),"%s/%s/serial",WR_USBIP_SYSFS,id);
 fp=fopen(path,"r");
 if (!fp) return;
 n=fread(bytes,1,sizeof(bytes),fp);
 if (ferror(fp) || n==sizeof(bytes)) { fclose(fp); return; }
 fclose(fp);
 if (n && bytes[n-1]=='\n') n--;
 if (!n || n>256) return;
 for (i=0;i<n;i++) if (bytes[i]<32 || bytes[i]==127) return;
 for (i=0;i<n;i++) { out[2*i]=hex[bytes[i]>>4]; out[2*i+1]=hex[bytes[i]&15]; }
 out[2*n]=0;
}
static int ej_wr_usbip_inventory(int eid, webs_t wp, int argc, char **argv)
{
 struct wr_usbip_device { char id[32], vendor[5], product[5], klass[3]; int exported; } rows[64];
 DIR *dir;
 struct dirent *entry;
 int count=0, visited=0, truncated=0, scan_error=0, i;
 (void)eid; (void)argv;
 if (argc) return websWrite(wp, "{\"error\":\"invalid_request\"}");
 dir = opendir(WR_USBIP_SYSFS);
 if (!dir) return websWrite(wp, "{\"error\":\"source_unavailable\"}");
 for (;;) {
  char path[256], driver[256];
  ssize_t length;
  struct wr_usbip_device *row;
  errno=0; entry=readdir(dir);
  if (!entry) { scan_error=errno!=0; break; }
  if (++visited>256) { truncated=1; break; }
  if (!wr_usbip_busid(entry->d_name)) continue;
  if (count==64) { truncated=1; break; }
  row=&rows[count]; memset(row,0,sizeof(*row));
  memcpy(row->id,entry->d_name,strlen(entry->d_name)+1);
  wr_usbip_hex(row->id,"idVendor",row->vendor,4);
  wr_usbip_hex(row->id,"idProduct",row->product,4);
  wr_usbip_hex(row->id,"bDeviceClass",row->klass,2);
  if (!strcmp(row->klass,"09")) continue; /* USB hubs are not export targets. */
  snprintf(path,sizeof(path),"%s/%s/driver",WR_USBIP_SYSFS,row->id);
  length=readlink(path,driver,sizeof(driver)-1);
  row->exported=2;
  if (length>=0 && length<(ssize_t)sizeof(driver)-1) {
   const char *tail;
   driver[length]=0; tail=strrchr(driver,'/');
   row->exported=!strcmp(tail?tail+1:driver,"usbip-host") ? 1 : 0;
  } else if (length<0 && errno==ENOENT) row->exported=0;
  count++;
 }
 closedir(dir);
 if (scan_error) return websWrite(wp,"{\"error\":\"source_unavailable\"}");
 websWrite(wp,"{\"devices\":[");
 for (i=0;i<count;i++) {
  char serial_hex[513];
  wr_usbip_serial_hex(rows[i].id,serial_hex);
  /* Only validated bus IDs and hexadecimal attributes enter JSON strings. */
  websWrite(wp,"%s{\"busid\":\"%s\",\"vendor\":\"%s\",\"product\":\"%s\",\"class\":\"%s\",\"exported\":%d,\"serial_hex\":\"%s\"}",
   i?",":"",rows[i].id,rows[i].vendor,rows[i].product,rows[i].klass,rows[i].exported,serial_hex);
 }
 return websWrite(wp,"],\"truncated\":%s}",truncated?"true":"false");
}
