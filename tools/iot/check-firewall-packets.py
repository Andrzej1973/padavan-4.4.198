#!/usr/bin/env python3
"""Host-kernel packet evidence in a disposable namespace; no router claim."""
import ctypes,os,select,socket,subprocess,sys,json
from pathlib import Path
if os.geteuid()!=0 or not os.environ.get('WR_IOT_PARENT_NETNS') or os.readlink('/proc/self/ns/net')==os.environ['WR_IOT_PARENT_NETNS']:
 raise SystemExit('Requires root inside a newly unshared network namespace')
root=Path(sys.argv[1]).resolve();servers=[];checks={};libc=ctypes.CDLL(None,use_errno=True)
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True)
run('mount','--make-rprivate','/')
run('mount','-t','tmpfs','tmpfs','/run/netns')
run('ip','link','set','lo','up')
for name in ('iot','lan','wan'):
 run('ip','netns','add',name);run('ip','-n',name,'link','set','lo','up')
def link(name,outer,peer,bridge,address,client):
 if bridge:
  run('ip','link','add',bridge,'type','bridge');run('ip','link','set',bridge,'up')
 run('ip','link','add',outer,'type','veth','peer','name',peer)
 run('ip','link','set',peer,'netns',name)
 if bridge:run('ip','link','set',outer,'master',bridge)
 run('ip','link','set',outer,'up');run('ip','addr','add',address,'dev',bridge or outer)
 run('ip','-n',name,'link','set',peer,'name','eth0');run('ip','-n',name,'link','set','eth0','up')
 run('ip','-n',name,'addr','add',client,'dev','eth0')
 run('ip','-n',name,'route','add','default','via',address.split('/')[0])
link('iot','iot-port','iot-peer','br-iot','192.168.50.1/24','192.168.50.20/24')
link('lan','lan-port','lan-peer','br0','192.168.1.1/24','192.168.1.2/24')
link('wan','eth2.2','wan-peer',None,'203.0.113.1/24','203.0.113.2/24')
run('sysctl','-w','net.ipv4.ip_forward=1')
run('ip','-6','addr','add','fd50::1/64','dev','br-iot')
run('ip','-n','iot','-6','addr','add','fd50::20/64','dev','eth0')
server_code="""import socket,threading,sys
s=socket.socket(socket.AF_INET6 if ':' in sys.argv[1] else socket.AF_INET);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind((sys.argv[1],int(sys.argv[2])));s.listen();print('READY',flush=True)
def echo(c):
 try:
  while True:
   data=c.recv(1024)
   if not data:break
   c.sendall(data)
 finally:c.close()
while True:
 c,_=s.accept();threading.Thread(target=echo,args=(c,),daemon=True).start()
"""
def server(name,address,port):
 args=([sys.executable,'-u','-c',server_code,address,str(port)])
 if name:args=['ip','netns','exec',name]+args
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);servers.append(p)
 if not select.select([p.stdout],[],[],5)[0] or p.stdout.readline().strip()!='READY':raise RuntimeError('Test server failed to start')
udp_code="""import socket,sys
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind((sys.argv[1],int(sys.argv[2])));print('READY',flush=True)
while True:
 data,peer=s.recvfrom(1024);s.sendto(data,peer)
"""
def udp_server(name,address,port):
 args=[sys.executable,'-u','-c',udp_code,address,str(port)]
 if name:args=['ip','netns','exec',name]+args
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);servers.append(p)
 if not select.select([p.stdout],[],[],5)[0] or p.stdout.readline().strip()!='READY':raise RuntimeError('UDP test server failed to start')
original=os.open('/proc/self/ns/net',os.O_RDONLY)
def switch(fd):
 if libc.setns(fd,0):raise OSError(ctypes.get_errno(),'setns failed')
def connect(name,address,port,family=socket.AF_INET,kind=socket.SOCK_STREAM,source_port=0):
 fd=os.open('/run/netns/'+name,os.O_RDONLY);s=None
 try:
  switch(fd);s=socket.socket(family,kind);s.settimeout(1)
  if source_port:s.bind(('',source_port))
  s.connect((address,port));return s
 except Exception:
  if s:s.close()
  raise
 finally:switch(original);os.close(fd)
def echo(name,address,port,family=socket.AF_INET,kind=socket.SOCK_STREAM,source_port=0):
 try:
  with connect(name,address,port,family,kind,source_port) as s:s.sendall(b'IOT');return s.recv(3)==b'IOT'
 except (TimeoutError,ConnectionError,OSError):return False
try:
 server(None,'192.168.50.1',53);server(None,'192.168.50.1',8080)
 server('lan','192.168.1.2',8080);server('wan','203.0.113.2',8080);server('iot','192.168.50.20',8080)
 server(None,'fd50::1',8081)
 udp_server(None,'192.168.50.1',53);udp_server(None,'192.168.50.1',67)
 udp_server('wan','203.0.113.2',8080);udp_server('lan','192.168.1.2',8080)
 udp_paths=[('iot','192.168.50.1',53,socket.AF_INET,socket.SOCK_DGRAM,0),('iot','192.168.50.1',67,socket.AF_INET,socket.SOCK_DGRAM,68),('iot','192.168.50.1',67,socket.AF_INET,socket.SOCK_DGRAM,1068),('iot','203.0.113.2',8080,socket.AF_INET,socket.SOCK_DGRAM,0),('iot','192.168.1.2',8080,socket.AF_INET,socket.SOCK_DGRAM,0)]
 for path in udp_paths:assert echo(*path),('UDP baseline absent',path)
 ipv6_path=('iot','fd50::1',8081,socket.AF_INET6)
 assert echo(*ipv6_path),'IPv6 baseline absent'
 paths=[('iot','192.168.50.1',53),('iot','192.168.50.1',8080),('iot','192.168.1.2',8080),('iot','203.0.113.2',8080),('lan','192.168.50.20',8080),('wan','192.168.50.20',8080),('lan','203.0.113.2',8080)]
 for path in paths:assert echo(*path),('Baseline connectivity absent',path)
 stale=connect('iot','192.168.1.2',8080);stale.sendall(b'OLD');assert stale.recv(3)==b'OLD'
 with (root/'iot-filter.v4').open() as f:subprocess.run(['iptables-legacy-restore'],stdin=f,check=True)
 with (root/'iot-filter.v6').open() as f:subprocess.run(['ip6tables-legacy-restore'],stdin=f,check=True)
 for key,path,expected in [
  ('tcp_dns_allowed',paths[0],True),('router_admin_blocked',paths[1],False),('lan_blocked',paths[2],False),
  ('wan_and_return_allowed',paths[3],True),('lan_unsolicited_blocked',paths[4],False),
  ('wan_unsolicited_blocked',paths[5],False),('main_lan_wan_preserved',paths[6],True)]:
  result=echo(*path);checks[key]=result==expected;assert checks[key],key
 stale.sendall(b'NEW')
 try:reply=stale.recv(3)
 except TimeoutError:reply=None
 checks['preexisting_lan_connection_blocked']=reply!=b'NEW';assert checks['preexisting_lan_connection_blocked'];stale.close()
 for key,path,expected in [('udp_dns_allowed',udp_paths[0],True),('dhcp_ports_allowed',udp_paths[1],True),('dhcp_wrong_source_port_blocked',udp_paths[2],False),('udp_wan_return_allowed',udp_paths[3],True),('udp_lan_blocked',udp_paths[4],False),('ipv6_router_blocked',ipv6_path,False)]:
  checks[key]=echo(*path)==expected;assert checks[key],key
 report={'checks':checks,'scope':'Host-kernel IPv4 TCP/UDP and DHCP-port filtering, stale conntrack isolation, IPv6 TCP router blocking; actual DNS/DHCP transactions and target runtime unverified','runtime_verified':False}
 (root/'iot-firewall-packets.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS host-kernel IoT packet isolation and preserved main LAN forwarding')
finally:
 for p in servers:
  p.terminate()
 for p in servers:
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 os.close(original)
