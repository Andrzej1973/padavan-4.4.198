#!/usr/bin/env python3
"""Add private USBIP export selection UI; saving never applies device actions."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():raise SystemExit(0)
root=a.source/'trunk/user/www';path=root/'n56u_ribbon_fixed/Advanced_Printer_others.asp'
text=path.read_text(encoding='utf-8');anchor='function initial(){';panel='<tr><th><#WRUSBIPActionTitle#>'
if text.count(anchor)!=1 or text.count(panel)!=1:raise SystemExit('USBIP settings view anchors changed')
keys=['title','help','ack','add','save','reload','remove','loading','loaded','unknown','invalid','draft','confirm','saved','unsynced','discard']
names=['Title','Help','Ack','Add','Save','Reload','Remove','Loading','Loaded','Unknown','Invalid','Draft','Confirm','Saved','Unsynced','Discard']
labels='var wrUSBIPSettingsLabels={'+','.join(k+':"<#WRUSBIPSettings'+n+'#>"' for k,n in zip(keys,names))+'};\n'
text=text.replace(anchor,labels+Path(__file__).with_name('settings-view.js').read_text(encoding='utf-8')+'\n'+anchor+'\n wrUSBIPSettingsLoad();',1)
text=text.replace(panel,'''<tr><th><#WRUSBIPSettingsTitle#></th><td>
 <p><#WRUSBIPSettingsHelp#></p>
 <table class="table"><tbody id="wr_usbip_settings_rows"></tbody></table>
 <button type="button" class="btn" id="wr_usbip_settings_add" onclick="wrUSBIPSettingsAdd()" disabled><#WRUSBIPSettingsAdd#></button>
 <button type="button" class="btn" onclick="wrUSBIPSettingsLoad()"><#WRUSBIPSettingsReload#></button>
 <label><input type="checkbox" id="wr_usbip_settings_ack"> <#WRUSBIPSettingsAck#></label>
 <button type="button" class="btn" id="wr_usbip_settings_save" onclick="wrUSBIPSettingsSave()" disabled><#WRUSBIPSettingsSave#></button>
 <p id="wr_usbip_settings_result" role="status" aria-live="polite"><#WRUSBIPSettingsUnknown#></p>
 </td></tr>
 '''+panel,1)
translations={
 'EN.footer':['Saved USB/IP export selections','Stores selections only. No device is exported now by saving selections. Automatic export requires the separate restore setting. To preserve storage across reboot, use the router storage save control. Serial identity data is private.',
 'I confirm replacing the saved export selections.','Add the currently selected device','Save selections','Reload selections','Remove','Reading or saving…','Selections loaded.','Result unknown. Reload before saving again.','A fresh device with a valid unique serial and free slot is required.','Draft changed; not saved.','Confirm the change and use an authorized session.','Saved in storage RAM; not applied or committed to flash.','File replaced, but synchronization is unconfirmed. Reload to check.','Discard unsaved changes and reload?'],
 'UK.dict':['Збережений вибір USB/IP-експорту','Лише збереження вибору. Пристрій зараз не експортується; саме збереження не вмикає експорт. Автоматичний експорт потребує окремого налаштування відновлення. Для збереження сховища після перезавантаження скористайтеся записом сховища роутера. Серійні ідентифікатори приватні.',
 'Підтверджую заміну збереженого вибору експорту.','Додати поточний вибраний пристрій','Зберегти вибір','Перечитати вибір','Прибрати','Читання або збереження…','Вибір завантажено.','Результат невідомий. Перед повторним збереженням перечитайте дані.','Потрібні свіжі дані пристрою, коректний унікальний серійний номер і вільний слот.','Чернетку змінено, але не збережено.','Підтвердіть зміну та використайте дозволений сеанс.','Збережено в оперативному сховищі; не застосовано й не записано у флеш.','Файл замінено, але синхронізацію не підтверджено. Перечитайте дані.','Відкинути незбережені зміни та перечитати?'],
 'RU.dict':['Сохранённый выбор USB/IP-экспорта','Только сохранение выбора. Устройство сейчас не экспортируется; само сохранение не включает экспорт. Автоматический экспорт требует отдельной настройки восстановления. Для сохранения хранилища после перезагрузки используйте запись хранилища роутера. Серийные идентификаторы приватны.',
 'Подтверждаю замену сохранённого выбора экспорта.','Добавить текущее выбранное устройство','Сохранить выбор','Перечитать выбор','Убрать','Чтение или сохранение…','Выбор загружен.','Результат неизвестен. Перед повторным сохранением перечитайте данные.','Нужны свежие данные устройства, корректный уникальный серийный номер и свободный слот.','Черновик изменён, но не сохранён.','Подтвердите изменение и используйте разрешённый сеанс.','Сохранено в оперативном хранилище; не применено и не записано во флеш.','Файл заменён, но синхронизация не подтверждена. Перечитайте данные.','Отбросить несохранённые изменения и перечитать?']}
changes=[(path,text)]
for name,values in translations.items():
 if len(values)!=len(names):raise SystemExit('USBIP settings translation count mismatch')
 target=root/'dict'/name;dictionary=target.read_text(encoding='utf-8')
 if 'WRUSBIPSettingsTitle=' in dictionary:raise SystemExit('Settings labels already installed')
 changes.append((target,dictionary.rstrip()+'\n'+'\n'.join('WRUSBIPSettings'+k+'='+v for k,v in zip(names,values))+'\n'))
for path,text in changes:path.write_text(text,encoding='utf-8',newline='\n')
print('Prepared USBIP selection settings UI EN/UK/RU; no restore/device actions')
