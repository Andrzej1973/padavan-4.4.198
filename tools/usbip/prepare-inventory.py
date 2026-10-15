#!/usr/bin/env python3
"""Install bounded USB/IP inventory in the existing authenticated USB page."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--config',type=Path,required=True)
a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():
    raise SystemExit(0)
root=a.source/'trunk/user'
changes=[]
path=root/'httpd/web_ex.c'
text=path.read_text()
anchor='struct ej_handler ej_handlers[] =\n'
entry='\t{ "wr_usbip_state", ej_wr_usbip_state},\n'
if text.count(anchor)!=1 or text.count(entry)!=1 or 'ej_wr_usbip_inventory' in text:
    raise SystemExit('USB/IP inventory HTTP anchor changed')
code=Path(__file__).with_name('inventory.inc').read_text()
text=text.replace(anchor,code+'\n'+anchor).replace(entry,entry+'\t{ "wr_usbip_inventory", ej_wr_usbip_inventory},\n')
changes.append((path,text))
path=root/'www/n56u_ribbon_fixed/Advanced_Printer_others.asp'
text=path.read_text()
anchor='function initial(){'
panel='                                        <tr><th><#WRUSBIPCore#>'
if text.count(anchor)!=1 or text.count(panel)!=1:
    raise SystemExit('USB/IP inventory page anchor changed')
js=r'''
var wrUSBIPInventoryBusy=false;
function wrUSBIPInventoryRefresh() {
 if(wrUSBIPInventoryBusy || document.hidden) return;
 wrUSBIPInventoryBusy=true;
 var view=$j('#wr_usbip_inventory');
 view.text('<#WRUSBIPUnknown#>');
 $j.ajax({url:'/update.cgi',data:{output:'wr_usbip_inventory'},dataType:'json',cache:false,timeout:5000})
 .done(function(reply) {
  if(!reply || !Array.isArray(reply.devices) || reply.devices.length>64 || typeof reply.truncated!=='boolean') return;
  var lines=[];
  for(var i=0;i<reply.devices.length;i++) {
   var row=reply.devices[i];
   if(!row || typeof row.busid!=='string' || !/^[0-9]+-[0-9]+(\.[0-9]+)*$/.test(row.busid) || row.busid.length>31 ||
      typeof row.vendor!=='string' || !/^([0-9a-fA-F]{4})?$/.test(row.vendor) ||
      typeof row.product!=='string' || !/^([0-9a-fA-F]{4})?$/.test(row.product) ||
      [0,1,2].indexOf(row.exported)<0) return;
   lines.push(row.busid+'  '+(row.vendor||'?')+':'+(row.product||'?')+'  '+
    (row.exported===1?'<#WRUSBIPExported#>':row.exported===0?'<#WRUSBIPNotExported#>':'<#WRUSBIPUnknown#>'));
  }
  view.text((lines.length?lines.join('\n'):'<#WRUSBIPNoDevices#>')+(reply.truncated?'\n<#WRUSBIPTruncated#>':''));
 })
 .always(function(){wrUSBIPInventoryBusy=false;});
}
'''
text=text.replace(anchor,js+'\n'+anchor+'\n wrUSBIPInventoryRefresh();')
text=text.replace(panel,'''                                        <tr><th><#WRUSBIPDevices#></th><td>
                                            <pre id="wr_usbip_inventory"><#WRUSBIPUnknown#></pre>
                                            <button type="button" class="btn" onclick="wrUSBIPInventoryRefresh()"><#WRUSBIPRefresh#></button>
                                        </td></tr>
'''+panel)
changes.append((path,text))
keys=['Devices','Exported','NotExported','NoDevices','Truncated']
for name,labels in [
 ('EN.footer',['Local USB devices (bus / vendor:product / export driver)','Bound to USB/IP export driver','Not bound to USB/IP export driver','No devices observed (USB hubs excluded)','List limit reached; result is incomplete']),
 ('UK.dict',['Локальні USB-пристрої (шина / виробник:пристрій / драйвер експорту)','Прив’язано до драйвера експорту USB/IP','Не прив’язано до драйвера експорту USB/IP','Пристроїв не виявлено (USB-концентратори виключено)','Досягнуто межі списку; результат неповний']),
 ('RU.dict',['Локальные USB-устройства (шина / производитель:устройство / драйвер экспорта)','Привязано к драйверу экспорта USB/IP','Не привязано к драйверу экспорта USB/IP','Устройства не обнаружены (USB-концентраторы исключены)','Достигнут предел списка; результат неполный'])]:
    path=root/'www/dict'/name
    text=path.read_text()
    if 'WRUSBIPDevices=' in text: raise SystemExit('Inventory labels already present')
    changes.append((path,text.rstrip('\n')+'\n'+'\n'.join('WRUSBIP'+k+'='+v for k,v in zip(keys,labels))+'\n'))
for path,text in changes:path.write_text(text)
print('Prepared bounded read-only USB/IP inventory and EN/UK/RU view')
