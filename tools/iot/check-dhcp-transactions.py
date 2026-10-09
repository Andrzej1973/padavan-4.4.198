#!/usr/bin/env python3
"""Pinned native dnsmasq DHCP/DNS transactions in disposable namespaces."""
import ctypes,json,os,socket,struct,subprocess,sys,time
from pathlib import Path
if os.geteuid()!=0 or not os.environ.get('WR_IOT_PARENT_NETNS') or os.readlink('/proc/self/ns/net')==os.environ['WR_IOT_PARENT_NETNS']:
 raise SystemExit('Requires root in a new isolated network namespace')
r=Path(sys.argv[1]).resolve();daemon=Path(sys.argv[2]).resolve();checks={};libc=ctypes.CDLL(None,use_errno=True)
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True)
run('mount','--make-rprivate','/');run('mount','-t','sysfs','sysfs','/sys');run('mount','-t','tmpfs','tmpfs','/run/netns')
run('ip','link','set','lo','up');run(str(r/'check-iot-bridge'),'prepare')
run('ip','link','add','br0','type','bridge');run('ip','addr','add','192.168.1.1/24','dev','br0')
for name,port,peer in [('iot','ra2','iot-peer'),('lan','lan-port','lan-peer')]:
 run('ip','netns','add',name);run('ip','-n',name,'link','set','lo','up')
 run('ip','link','add',port,'type','veth','peer','name',peer);run('ip','link','set',peer,'netns',name)
 run('ip','-n',name,'link','set',peer,'name','eth0');run('ip','-n',name,'link','set','eth0','up')
 if name=='iot':run(str(r/'check-iot-bridge'),'attach')
 else:run('ip','link','set',port,'master','br0')
for version,restore in [('4','iptables-legacy-restore'),('6','ip6tables-legacy-restore')]:
 with (r/('iot-filter.v'+version)).open() as f:subprocess.run([restore],stdin=f,check=True)
for device in ('br0','br-iot','lan-port','ra2'):run('ip','link','set',device,'up')
config=(r/'iot-dnsmasq.conf').read_text().replace('port=0','port=53')
config+='no-resolv\nhost-record=iot-fixture.invalid,192.0.2.10\ndhcp-option=tag:lan,3,192.168.1.1\ndhcp-option=tag:lan,6,192.168.1.1\n'
conf=r/'iot-dnsmasq-transactions.conf';conf.write_text(config)
original=os.open('/proc/self/ns/net',os.O_RDONLY)
def switch(fd):
 if libc.setns(fd,0):raise OSError(ctypes.get_errno(),'setns failed')
def client_socket(name,port=0,broadcast=False):
 fd=os.open('/run/netns/'+name,os.O_RDONLY) if name else original
 try:
  switch(fd);s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(1)
  if broadcast:s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1);s.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,b'eth0\0')
  s.bind(('0.0.0.0',port));return s
 finally:
  switch(original)
  if name:os.close(fd)
def options(data):
 result={};i=240
 while i<len(data):
  key=data[i];i+=1
  if key==255:break
  if key==0:continue
  if i>=len(data):raise ValueError('Truncated DHCP option')
  length=data[i];i+=1
  if i+length>len(data):raise ValueError('Truncated DHCP value')
  result[key]=data[i:i+length];i+=length
 return result
def lease(name,mac,gateway,prefix,xid):
 header=struct.pack('!BBBBIHH4s4s4s4s16s64s128s',1,1,6,0,xid,0,0x8000,b'\0'*4,b'\0'*4,b'\0'*4,b'\0'*4,mac+b'\0'*10,b'\0'*64,b'\0'*128)
 cookie=b'\x63\x82\x53\x63';common=b'\x3d\x07\x01'+mac+b'\x37\x04\x01\x03\x06\x36'
 with client_socket(name,68,True) as s:
  def exchange(kind,extra,wanted):
   packet=header+cookie+b'\x35\x01'+bytes([kind])+common+extra+b'\xff'
   for _ in range(3):
    s.sendto(packet,('255.255.255.255',67));deadline=time.monotonic()+1
    while time.monotonic()<deadline:
     try:data,_=s.recvfrom(4096)
     except TimeoutError:break
     if len(data)<240 or data[0]!=2 or struct.unpack('!I',data[4:8])[0]!=xid or data[28:34]!=mac or data[236:240]!=cookie:continue
     opt=options(data)
     if opt.get(53)==bytes([wanted]):return data,opt
   raise RuntimeError('DHCP transaction timed out: '+name)
  offer,opt=exchange(1,b'',2);address=socket.inet_ntoa(offer[16:20]);assert address.startswith(prefix) and 20<=int(address.split('.')[-1])<=200
  assert opt[54]==socket.inet_aton(gateway)
  ack,opt=exchange(3,b'\x32\x04'+offer[16:20]+b'\x36\x04'+socket.inet_aton(gateway),5)
  assert socket.inet_ntoa(ack[16:20])==address
  assert opt[1]==socket.inet_aton('255.255.255.0') and opt[3]==socket.inet_aton(gateway) and opt[6]==socket.inet_aton(gateway)
 checks[name+'_dhcp_offer_ack_pool_options']=True
 run('ip','-n',name,'addr','add',address+'/24','dev','eth0');run('ip','-n',name,'route','add','default','via',gateway)
def dns(name,gateway):
 query=struct.pack('!6H',0x1234,0x0100,1,0,0,0)+b'\x0biot-fixture\x07invalid\0'+struct.pack('!HH',1,1)
 with client_socket(name) as s:s.sendto(query,(gateway,53));data,_=s.recvfrom(4096)
 ident,flags,qd,an,_,_=struct.unpack('!6H',data[:12]);assert ident==0x1234 and flags&0x8000 and flags&15==0 and qd==1 and an>=1
 assert data[-4:]==socket.inet_aton('192.0.2.10')
log=(r/'iot-dnsmasq-transactions.log').open('w');process=None
try:
 process=subprocess.Popen([str(daemon),'--keep-in-foreground','--user=root','--conf-file='+str(conf),'--pid-file='+str(r/'iot-dnsmasq.pid'),'--dhcp-leasefile='+str(r/'iot-dnsmasq.leases')],stdout=log,stderr=log)
 deadline=time.monotonic()+5
 while True:
  if process.poll() is not None:raise RuntimeError('dnsmasq exited; inspect transaction log')
  try:dns(None,'192.168.1.1');break
  except (TimeoutError,OSError):
   if time.monotonic()>deadline:raise
 lease('iot',bytes.fromhex('020000000050'),'192.168.50.1','192.168.50.',0x50505050)
 lease('lan',bytes.fromhex('020000000001'),'192.168.1.1','192.168.1.',0x10101010)
 dns('iot','192.168.50.1');checks['iot_dns_transaction']=True
 dns('lan','192.168.1.1');checks['main_lan_dns_preserved']=True
 (r/'iot-dhcp-transactions.json').write_text(json.dumps({'checks':checks,'scope':'Pinned native dnsmasq host DHCP OFFER/ACK and DNS over isolated IoT/LAN with generated firewall; production RC and target runtime unverified','runtime_verified':False},indent=2)+'\n')
 print('PASS pinned dnsmasq IoT and main LAN DHCP/DNS transactions with isolation rules')
finally:
 if process:
  process.terminate()
  try:process.wait(timeout=3)
  except subprocess.TimeoutExpired:process.kill();process.wait()
 log.close();os.close(original)
