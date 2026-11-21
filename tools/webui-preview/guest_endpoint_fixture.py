"""Join actual generated HTTP/body/CGI/apply functions; substitute external systems only."""
def endpoint_fixture(template, server, source, cgi, here):
    base=template.split('static const char *guest_values[]')[0]
    base=base.replace('static int shared_mode,source_band;static const char *posted_key;','')
    base=base.replace('static int nvram_set(const char *name,const char *value){int i;', 'static const char *fail_nvram_key;\nstatic int nvram_set(const char *name,const char *value){int i;if(fail_nvram_key&&!strcmp(name,fail_nvram_key))return -1;')
    base=base.replace('static char *nvram_safe_get(const char *name){int i;', 'static int secret_reads;\nstatic char *nvram_safe_get(const char *name){int i;if(strstr(name,\"_guest_wpa_psk\"))secret_reads++;')
    base=base.replace('static char *guest_cgi(webs_t,char *,char *);\nstatic char *websGetVar(webs_t wp,char *name,char *fallback){return guest_cgi(wp,name,fallback);}',
                      'static char *websGetVar(webs_t wp,char *name,char *fallback){char *v=get_cgi(name);(void)wp;return v?v:fallback;}')
    base=base.replace(' int wr_modern_guest_post_allowed(void){return 1;}','').replace(' void wr_modern_guest_input_fail(void){}','')
    http=(here/'guest-http-fixture.c.inc').read_text().split('/* ACTUAL_HANDLE_REQUEST */')[0]
    http=http.replace('static void wr_modern_body_clear(void){}','')
    http=http.replace('static struct mime_handler mime_handlers[]={', 'static struct mime_handler mime_handlers[]={\n {\"wr_modern_guest_apply.json\",\"application/json\",NULL,input,do_wr_modern_guest_apply,1},')
    http=http.replace('static void do_ej(const char *file,FILE *stream){(void)file;(void)stream;outputs++;observed=wr_modern_guest_post_allowed();}',
                      'static void do_ej(const char *file,FILE *stream){(void)file;outputs++;observed=wr_modern_guest_post_allowed();update_variables_ex(0,(void *)stream,0,NULL);asus_nvram_commit(0,(void *)stream,0,NULL);ej_notify_services(0,(void *)stream,0,NULL);}')
    http=http.replace('static void input(const char *file,FILE *stream,int length,char *boundary){(void)file;(void)boundary;inputs++;eat_post_data(stream,length);}',
                      'static void input(const char *file,FILE *stream,int length,char *boundary){inputs++;do_html_apply_post(file,stream,length,boundary);}')
    http=http.replace('int wr_modern_guest_post_allowed(void){return wr_modern_guest_post_authorized;}',
                      'int wr_modern_guest_post_allowed(void){return wr_modern_guest_post_authorized;}\nvoid wr_modern_guest_input_fail(void){wr_modern_input_rejected=1;}')
    def function(text, marker, prefix=''):
        a=text.index(marker);b=text.index('\n}',a)+2
        return prefix+text[a:b]
    input_fn=function(source,'do_html_apply_post(const char *url','static void\n')
    clear=function(source,'void wr_modern_body_clear(void)')
    request=function(server,'handle_request(FILE *conn_fp','static void\n')
    json_output=(here/'guest-json-output.c.inc').read_text()
    json_output='static int fail_sink;\nstatic FILE *fixture_open_sink(const char *path,const char *mode){return fail_sink?NULL:fopen(path,mode); }\n'+json_output.replace('sink=fopen("/dev/null","w");','sink=fixture_open_sink("/dev/null","w");')
    body_globals='''
#define MIN(a,b) ((int)(a)<(int)(b)?(int)(a):(int)(b))
static char post_buf[65535];static int group_del_map[1];
static void websScan(const char *v){(void)v;abort();}
'''
    return '#define _GNU_SOURCE\n'+cgi+'\n'+base+body_globals+'\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n'+input_fn+'\n#pragma GCC diagnostic pop\n'+clear+'\n'+json_output+'\n'+http+'\n'+request+'\n'+(here/'guest-endpoint-main.c.inc').read_text()
