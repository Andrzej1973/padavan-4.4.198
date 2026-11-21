from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
code=(here/'check-config-view-endpoint.c').read_text()
anchor='static char socket_path[108];'
assert code.count(anchor)==1
code=code.replace(anchor,anchor+'''
static const char *query_directory;
static pid_t query_pid;
#define WR_IOT_CONFIG_VIEW_DIRECTORY query_directory
#define WR_IOT_HTTP_RC_PID query_pid
#define WR_IOT_HTTP_RC_UID getuid()
#include "config-view-client.c"
''',1)
anchor='int ok=wr_iot_config_view_endpoint_query(directory,child,getuid(),&view,revision);'
assert code.count(anchor)==1
code=code.replace(anchor,'query_directory=directory;query_pid=child;int ok=wr_iot_http_view_read(&view,revision);',1)
production=(here/'config-view-client.c').read_text()
assert '#define WR_IOT_HTTP_RC_PID 1\n' in production and '#define WR_IOT_HTTP_RC_UID 0\n' in production
with tempfile.TemporaryDirectory(prefix='wr-view-client-build-') as directory:
 root=Path(directory);source=root/'check.c';source.write_text(code);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(source),
  *[str(here/name) for name in ('config-view-endpoint.c','config-view-channel.c','status-endpoint.c','status-channel.c')],
  '-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual HTTP view client wrapper: configured/absent/refused responses and replacement safety; production defaults inspected PID1/UID0, test uses explicit fork peer')
