#!/usr/bin/env python3
"""Add explicit device actions and asynchronous result display to the USB page."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():raise SystemExit(0)
root=a.source/'trunk/user/www';path=root/'n56u_ribbon_fixed/Advanced_Printer_others.asp'
text=path.read_text()
replacements=[
 ('function initial(){', 'var wrUSBIPActionToken=<% wr_usbip_token(); %>;\nvar wrUSBIPActionLabels={pending:"<#WRUSBIPActionPending#>",done:"<#WRUSBIPActionDone#>",failed:"<#WRUSBIPActionFailed#>",unknown:"<#WRUSBIPActionUnknown#>"};\n'+Path(__file__).with_name('action-view.js').read_text()+'\nfunction initial(){'),
 (' wrUSBIPInventoryBusy=true;', ' wrUSBIPInventoryBusy=true;\n wrUSBIPActionDevices(null);'),
 ("  view.text((lines.length?", "  wrUSBIPActionDevices(reply.devices);\n  view.text((lines.length?"),
 (' $j("#wr_usbip_daemon").text(wrUSBIPValue(value.daemon, true));', ' $j("#wr_usbip_daemon").text(wrUSBIPValue(value.daemon, true));\n wrUSBIPActionDaemon=value.daemon;wrUSBIPActionUpdate();'),
 ('                                        <tr><th><#WRUSBIPCore#>', '''                                        <tr><th><#WRUSBIPActionTitle#></th><td>
                                            <select id="wr_usbip_device_select" onchange="wrUSBIPActionUpdate()" disabled></select>
                                            <label><input type="checkbox" id="wr_usbip_ack" onchange="wrUSBIPActionUpdate()"> <#WRUSBIPActionAck#></label>
                                            <button type="button" class="btn" id="wr_usbip_bind" onclick="wrUSBIPActionSubmit('bind')" disabled><#WRUSBIPBind#></button>
                                            <button type="button" class="btn" id="wr_usbip_unbind" onclick="wrUSBIPActionSubmit('unbind')" disabled><#WRUSBIPUnbind#></button>
                                            <p id="wr_usbip_action_result" role="status"><#WRUSBIPActionUnknown#></p>
                                            <button type="button" class="btn" onclick="wrUSBIPActionPoll()"><#WRUSBIPActionCheck#></button>
                                        </td></tr>
                                        <tr><th><#WRUSBIPCore#>''')]
for anchor,replacement in replacements:
    if text.count(anchor)!=1:raise SystemExit('USB/IP action view anchor changed: '+anchor)
    text=text.replace(anchor,replacement)
changes=[(path,text)]
keys=['ActionTitle','ActionAck','Bind','Unbind','ActionPending','ActionDone','ActionFailed','ActionUnknown','ActionCheck']
for name,values in [
 ('EN.footer',['USB/IP device actions','I confirm changing the selected USB device driver; local use may be interrupted.','Export device','Return device locally','Operation pending; do not repeat.','Controller completed. Check the refreshed binding; USB transfer is not verified.','Controller failed or result unconfirmed. Check the device list and log.','No confirmed result. A timeout does not prove that the operation stopped.','Check operation result']),
 ('UK.dict',['Дії з USB/IP-пристроєм','Підтверджую зміну драйвера вибраного USB-пристрою; локальна робота з ним може перерватися.','Експортувати пристрій','Повернути локально','Операція виконується; не повторюйте.','Контролер завершив дію. Перевірте оновлену прив’язку; передача USB не підтверджена.','Помилка контролера або непідтверджений результат. Перевірте список пристроїв і журнал.','Немає підтвердженого результату. Тайм-аут не означає зупинку операції.','Перевірити результат']),
 ('RU.dict',['Действия с USB/IP-устройством','Подтверждаю изменение драйвера выбранного USB-устройства; локальная работа с ним может прерваться.','Экспортировать устройство','Вернуть локально','Операция выполняется; не повторяйте.','Контроллер завершил действие. Проверьте обновлённую привязку; передача USB не подтверждена.','Ошибка контроллера или неподтверждённый результат. Проверьте список устройств и журнал.','Нет подтверждённого результата. Тайм-аут не означает остановку операции.','Проверить результат'])]:
    path=root/'dict'/name;text=path.read_text()
    if 'WRUSBIPActionTitle=' in text:raise SystemExit('USB/IP action labels already present')
    changes.append((path,text.rstrip('\n')+'\n'+'\n'.join('WRUSBIP'+k+'='+v for k,v in zip(keys,values))+'\n'))
for path,text in changes:path.write_text(text)
print('Prepared USB/IP action selection, confirmation and asynchronous result view EN/UK/RU')
