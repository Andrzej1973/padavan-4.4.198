"""Real local sockets/Edge with actual candidate HTTP/CGI/auth; external services substituted."""
import http.server,json,pathlib,shutil,subprocess,tarfile,tempfile,threading,html,re

def run_browser(joined,server,root,here,archive_path):
    with tarfile.open(archive_path) as archive:
        base64=archive.extractfile('trunk/user/httpd/base64.c').read().decode()
    a=server.index('static int\nauth_check(');b=server.index('\n}',a)+2
    auth=server[a:b].replace('auth_check(', 'fixture_auth_check(',1)
    old='static int auth_check(const char *value){auth_calls++;return value&&strstr(value,"Basic fixture-good");}'
    assert old in joined
    actual_auth=base64+'\nstatic const char *auth_basic_data="fixture:fixture-password";\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wpointer-sign"\n'+auth+'\n#pragma GCC diagnostic pop\nstatic int auth_check(const char *v){auth_calls++;return fixture_auth_check(v);}'
    native=joined.replace(old,actual_auth)
    old='static void send_headers(int status,const char *title,const char *extra,const char *mime,struct stat *st,FILE *stream){(void)title;(void)extra;(void)mime;(void)st;(void)stream;status_code=status;}'
    assert old in native
    native=native.replace(old,'static void send_headers(int status,const char *title,const char *extra,const char *mime,struct stat *st,FILE *stream){(void)st;status_code=status;fprintf(stream,"HTTP/1.1 %d %s\\r\\nContent-Type: %s\\r\\nConnection: close\\r\\n%s\\r\\n",status,title,mime?mime:"text/plain",extra?extra:"");}')
    module=(here/'public/wifi.js').read_text().split("if (typeof document !== 'undefined')")[0]
    page=(here/'guest-browser-protocol.html').read_text()
    projection=(here/'wr-modern-http.inc').read_text()
    def function(marker):
        a=projection.index(marker);return projection[a:projection.index('\n}',a)+2]
    helpers='\n'.join(function(m) for m in ['static void wr_modern_json_string(','static void wr_modern_json_field(','static void wr_modern_guest_band('])
    assets='static int socket_posts,socket_options;\n'+helpers+'\n'+f'static const char fixture_js[]={json.dumps(module,ensure_ascii=False)};\nstatic const char fixture_page[]={json.dumps(page,ensure_ascii=False)};\n'
    assets+='''static void fixture_client(const char *u,FILE *s){(void)u;fputs(fixture_js,s);}
static void fixture_html(const char *u,FILE *s){(void)u;fputs(fixture_page,s);}
static void fixture_state(const char *u,FILE *s){(void)u;fputs("{\\\"guests\\\":{\\\"24\\\":",s);wr_modern_guest_band(s,"rt");fputs("}}",s);}
static void fixture_metrics(const char *u,FILE *s){(void)u;fprintf(s,"{\\\"posts\\\":%d,\\\"options\\\":%d,\\\"writes\\\":%d}",socket_posts,socket_options,writes);}
'''
    table='static struct mime_handler mime_handlers[]={'
    native=native.replace('struct mime_handler {',assets+'\nstruct mime_handler {',1)
    native=native.replace(table,table+'''
 {"fixture-client.js","text/javascript",NULL,NULL,fixture_client,0},
 {"fixture.html","text/html",NULL,NULL,fixture_html,0},
 {"fixture-state.json","application/json",NULL,NULL,fixture_state,1},
 {"fixture-metrics.json","application/json",NULL,NULL,fixture_metrics,1},''',1)
    native=native.replace('if (strcasecmp(method, "get") == 0)','if (!strcasecmp(method,"POST"))socket_posts++;\n if (!strcasecmp(method,"OPTIONS"))socket_options++;\n if (strcasecmp(method, "get") == 0)',1)
    native=native[:native.index('int main(void)')]+(here/'guest-socket-main.c.inc').read_text()
    (root/'socket-fixture.c').write_text(native)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(root/'socket-fixture.c'),'-o',str(root/'socket-fixture')],check=True)
    process=subprocess.Popen([str(root/'socket-fixture')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    class Attacker(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            payload=b'''<script>(async()=>{const target=new URL(location.href).searchParams.get('target');let blocked=false;try{await fetch(target+'/wr_modern_guest_apply.json',{method:'POST',headers:{'X-WR-Modern':'1',Authorization:'Basic '+btoa('fixture:fixture-password')},body:'wr_modern_guest_version=1',credentials:'omit'});}catch(_){blocked=true;}parent.postMessage({blocked},target);})();</script>'''
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(payload)
    attacker=http.server.ThreadingHTTPServer(('127.0.0.1',0),Attacker)
    threading.Thread(target=attacker.serve_forever,daemon=True).start()
    profile=None;report=None
    try:
        line=process.stdout.readline().strip();assert line.startswith('PORT '),line
        port=int(line.split()[1]);print('Local native HTTP fixture ready',flush=True)
        profile=pathlib.Path(tempfile.mkdtemp(prefix='wr-guest-socket-browser-',dir='/mnt/c/Users/ANDRZEJ/AppData/Local/Temp'))
        win=subprocess.check_output(['wslpath','-w',str(profile)],text=True).strip()
        url=f'http://127.0.0.1:{port}/fixture.html?attacker=http://127.0.0.1:{attacker.server_port}'
        result=subprocess.run(['/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions','--user-data-dir='+win,'--virtual-time-budget=12000','--dump-dom',url],capture_output=True,text=True,timeout=55)
        assert result.returncode==0,result.stderr[-1500:]
        assert 'data-status="pass"' in result.stdout,result.stdout[-2500:]
        match=re.search(r'<pre id="result">(.*?)</pre>',result.stdout,re.S);assert match
        report=json.loads(html.unescape(match.group(1)))
        report.update(scope='Local native HTTP/auth/CGI + Edge, fake NVRAM/RC/login provider/HTTP wrapper; no router',runtimeVerified=False)
        (root/'browser-result.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS real Edge/native sockets: same origin, UTF8, actual Basic decode, double click, stale reload, OPTIONS501/CORS blocked/no extra writes',flush=True)
        return report
    finally:
        attacker.shutdown();attacker.server_close();process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        errors=process.stderr.read()
        if 'ERROR: AddressSanitizer' in errors or 'runtime error:' in errors:raise RuntimeError(errors[-3000:])
        if profile and profile.exists():
            size=sum(f.stat().st_size for f in profile.rglob('*') if f.is_file() and not f.is_symlink())
            shutil.rmtree(profile);assert not profile.exists()
            if report is not None:report['browser_profile_removed_bytes']=size
            print('Removed owned browser profile bytes',size,flush=True)
