"use strict";

// Wi-Fi render/protocol helpers. Production remains read-only; Guest submission
// is opt-in through an injected candidate transport, never started on page load.
const WifiDemo = (() => {
  const commonKeys = ['ssid', 'auth_mode', 'wep_x', 'wpa_mode', 'crypto', 'wpa_psk'];
  const sections = {general:'Загальні', guest:'Гостьова', bridge:'Міст', mac:'Фільтр MAC-адрес', radius:'Налаштування RADIUS', advanced:'Професійно'};
  const basic = (ssid) => ({ssid, auth_mode:'psk', wep_x:'0', wpa_mode:'2', crypto:'aes', wpa_psk:'demo-password', radio_x:'0', closed:'0'});
  function makeState() {
    return {shared:false, common:basic('Home'), bands:{24:basic('Home-2.4G'), 5:basic('Home-5G')}, iot:{...basic('Home-IoT'), clientIsolation:'0', lanIsolation:'0'}};
  }
  function synchronize(state, planner) {
    planner('0', '1', 'rt', state.common);
    for (const band of Object.values(state.bands)) for (const key of commonKeys) band[key] = state.common[key];
    state.shared = true;
  }
  function route(hash) {
    const parts = hash.replace(/^#/, '').split('/');
    if (!parts[0]) return {view:'home'};
    if (parts[0] !== 'wifi') return {view:'external'};
    if (parts[1] === 'split' && ['24','5'].includes(parts[2])) return {view:'band', band:parts[2], section:Object.hasOwn(sections, parts[3]) ? parts[3] : 'general'};
    return {view:['common','split','iot'].includes(parts[1]) ? parts[1] : 'common'};
  }
  const publicFields=['ssid','auth_mode','wep_x','wpa_mode','crypto','radio_x','closed','channel','HT_BW','gmode','HT_EXTCHA'];
  function publicConfiguration(data) {
    const config=data?.wifiConfiguration;
    if(config?.schemaVersion!==1 || config.source!=='stored-nvram' || config.runtimeVerified!==false) return null;
    const bands={};
    for(const band of ['24','5']) {
      const values=config.bands?.[band];
      if(!values || !publicFields.every(key=>typeof values[key]==='string')) return null;
      bands[band]=Object.fromEntries(publicFields.map(key=>[key,values[key]]));
    }
    const guestFields=['enable','ssid','closed','auth_mode','wpa_mode','crypto','lan_isolate','ap_isolate','macrule','mcs_mode','date_x','time_x','time2_x'];
    const guests={};
    for(const band of ['24','5']) {
      const values=config.guests?.[band];
      guests[band]=values && guestFields.every(key=>typeof values[key]==='string')
        ? Object.fromEntries(guestFields.map(key=>[key,values[key]])) : null;
    }
    return {shared:['0','1'].includes(config.shared)?config.shared:null,bands,guests};
  }
  // Classic stores Sunday first; each interval is HHMMHHMM. Invalid stored
  // values stay unknown rather than silently becoming an enabled schedule.
  function guestSchedule(date, weekday, weekend) {
    const interval=value=>{
      if(typeof value!=='string' || !/^\d{8}$/.test(value)) return null;
      const parts=[0,2,4,6].map(i=>value.slice(i,i+2));
      if(Number(parts[0])>23 || Number(parts[2])>23 || Number(parts[1])>59 || Number(parts[3])>59) return null;
      return {start:parts[0]+':'+parts[1],end:parts[2]+':'+parts[3]};
    };
    return {
      days:typeof date==='string' && /^[01]{7}$/.test(date)
        ? Object.fromEntries(['sun','mon','tue','wed','thu','fri','sat'].map((day,i)=>[day,date[i]==='1'])) : null,
      weekday:interval(weekday),weekend:interval(weekend)
    };
  }
  const guestResultKeys=['schemaVersion','state','settingsMayHaveChanged','ramConfigurationMatches','flashCommit','serviceNotification','runtimeVerified','automaticRetry','nextAction'];
  const unknownGuestResult=()=>Object.freeze({state:'unknown',runtimeVerified:false,automaticRetry:false,requiresReload:true,message:'Результат не підтверджено. Перечитайте налаштування перед повторною спробою.'});
  function guestApplyResult(reply) {
    if(!reply || typeof reply!=='object' || Array.isArray(reply) ||
       Object.keys(reply).length!==guestResultKeys.length || !guestResultKeys.every(key=>Object.hasOwn(reply,key)) ||
       reply.schemaVersion!==1 || reply.runtimeVerified!==false || reply.automaticRetry!==false ||
       reply.nextAction!=='reload_configuration' || typeof reply.settingsMayHaveChanged!=='boolean' ||
       typeof reply.ramConfigurationMatches!=='boolean')return unknownGuestResult();
    const messages={configuration_matches:'Збережені налаштування відповідають запиту. Роботу мережі ще не підтверджено.',reload_required:'Налаштування змінилися або застаріли. Перечитайте їх перед новою спробою.',busy:'Попередня зміна ще не завершена. Перечитайте налаштування.',rejected:'Запит відхилено. Перечитайте налаштування й перевірте введені дані.',unconfirmed:'Результат не підтверджено; частина налаштувань могла змінитися. Перечитайте їх.',unavailable:'Застосування зараз недоступне. Перечитайте налаштування перед новою спробою.'};
    if(!Object.hasOwn(messages,reply.state) || reply.ramConfigurationMatches!==(reply.state==='configuration_matches') ||
       !['not_requested','manual_mode','requested_unverified'].includes(reply.flashCommit) ||
       !['not_requested','requested_unverified'].includes(reply.serviceNotification))return unknownGuestResult();
    if(reply.state!=='configuration_matches' && (reply.flashCommit!=='not_requested'||reply.serviceNotification!=='not_requested'))return unknownGuestResult();
    if(reply.state==='unconfirmed' ? !reply.settingsMayHaveChanged :
       reply.state!=='configuration_matches' && reply.settingsMayHaveChanged)return unknownGuestResult();
    if(!reply.settingsMayHaveChanged && (reply.flashCommit!=='not_requested'||reply.serviceNotification!=='not_requested'))return unknownGuestResult();
    return Object.freeze({state:reply.state,runtimeVerified:false,automaticRetry:false,requiresReload:true,
      settingsMayHaveChanged:reply.settingsMayHaveChanged,ramConfigurationMatches:reply.ramConfigurationMatches,
      flashCommit:reply.flashCommit,serviceNotification:reply.serviceNotification,message:messages[reply.state]});
  }
  // Opt-in one-shot controller. Production renderer does not instantiate it.
  // A fresh controller must be created after configuration is reread; never reset
  // a completed/unknown request and resend the old draft automatically.
  function guestSubmission(transmit,{timeoutMs=15000}={}) {
    if(typeof transmit!=='function' || !Number.isInteger(timeoutMs) || timeoutMs<1 || timeoutMs>60000)throw new TypeError('Invalid Guest transport');
    let state=Object.freeze({state:'ready',runtimeVerified:false,automaticRetry:false});
    return Object.freeze({getState:()=>state,submit:async body=>{
      if(state.state!=='ready')return false;
      state=Object.freeze({state:'pending',runtimeVerified:false,automaticRetry:false});
      const controller=new AbortController();let timer;
      const expired=Symbol('expired');
      try {
        const timeout=new Promise(resolve=>{timer=setTimeout(()=>{controller.abort();resolve(expired);},timeoutMs);});
        const reply=await Promise.race([Promise.resolve().then(()=>transmit(body,{signal:controller.signal})),timeout]);
        state=reply===expired?unknownGuestResult():guestApplyResult(reply);
      } catch (_) { state=unknownGuestResult(); }
      finally {clearTimeout(timer);}
      return state;
    }});
  }
  return {commonKeys, sections, makeState, synchronize, route, publicConfiguration, guestSchedule, guestApplyResult, guestSubmission};
})();
if (typeof module !== 'undefined') module.exports = WifiDemo;

if (typeof document !== 'undefined') (async () => {
  const response = await fetch('/wifi-schema.json', {credentials:'omit', cache:'no-store'});
  if (!response.ok) throw Error('Wi-Fi schema unavailable');
  const schema = await response.json();
  if (typeof schema.demo !== 'boolean') throw Error('Unmarked Wi-Fi schema');
  let configuration=null;
  if(!schema.demo) {
    try {
      const live=await fetch('/wr_modern.json',{credentials:'same-origin',cache:'no-store'});
      if(live.ok) configuration=WifiDemo.publicConfiguration(await live.json());
    } catch (_) { /* Keep navigation available; never substitute demo settings. */ }
  }
  const modeLabel = schema.demo ? 'DEMO' : 'READ-ONLY';
  const state = WifiDemo.makeState();
  const root = document.getElementById('modern-wifi');
  const home = document.getElementById('modern-home');
  const homeButton = document.querySelector('.nav-item');
  const wifiButton = document.getElementById('wifi-navigation');
  let notice = '';
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const go = (hash) => { location.hash = hash; };
  const nav = (title, hash, active) => {
    const link = element('a', title, 'wifi-tab' + (active ? ' selected' : ''));
    link.href = '#' + hash;
    if (active) link.setAttribute('aria-current', 'page');
    return link;
  };
  function field(form, target, key, title, options, type='text', disabled=false, maxLength) {
    if (options?.length === 2 && options.every(o => ['0','1'].includes(o[0])) && /Увімк|Вимк/.test(options[0][1])) { type='checkbox'; options=null; }
    const row = element('label', undefined, 'wifi-field');
    row.append(element('span', title));
    let input;
    if (options?.length) {
      input = element('select');
      input.append(new Option('Не задано в макеті', ''));
      for (const [value, text] of options) input.append(new Option(text, value));
    } else input = element(type === 'textarea' ? 'textarea' : 'input');
    if (input.tagName === 'INPUT') input.type = ['password', 'checkbox'].includes(type) ? type : 'text';
    input.name = key; input.dataset.key = key;
    input.autocomplete = 'off'; input.disabled = disabled;
    if (maxLength) input.maxLength = maxLength;
    if (type === 'checkbox') { input.checked = target[key] === '1'; input.setAttribute('role','switch'); }
    else input.value = target[key] ?? '';
    input.addEventListener('input', () => {
      target[key] = type === 'checkbox' ? (input.checked ? '1' : '0') : input.value;
      notice = '';
    });
    row.append(input); form.append(row);
  }
  const binary = [['0','Вимкнено'],['1','Увімкнено']];
  function basic(form, target, shared=false) {
    field(form,target,'radio_x','Увімкнення Wi-Fi',null,'checkbox',shared);
    field(form,target,'ssid','SSID',null,'text',false,32);
    field(form,target,'auth_mode','Метод автентифікації',[['open','Відкрита мережа'],['psk','WPA Personal']]);
    field(form,target,'wpa_mode','Версія WPA',[['2','WPA2'],['0','WPA / WPA2'],['1','WPA']]);
    field(form,target,'crypto','Шифрування',[['aes','AES'],['tkip','TKIP'],['tkip+aes','TKIP + AES']]);
    field(form,target,'wpa_psk','Пароль Wi-Fi',null,'password',false,64);
    field(form,target,'closed','Приховування SSID',null,'checkbox',shared);
  }
  function confirmDraft(form, action) {
    const button = element('button',action ? 'Перевірити чернетку '+modeLabel : 'Переглянути чернетку '+modeLabel,'primary-button');
    button.type='submit'; form.append(button);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const dialog = element('dialog', undefined, 'wifi-confirm');
      dialog.setAttribute('aria-label','Попередження перед застосуванням');
      dialog.append(element('h2','Зміни Wi-Fi можуть розірвати з’єднання'),element('p','Це лише '+modeLabel+'. Підтвердження перевіряє чернетку в пам’яті; роутер не змінюється.'));
      const cancel = element('button','Назад до редагування','wifi-tab'); cancel.type='button';
      const ok = element('button','Підтвердити '+modeLabel,'primary-button'); ok.type='button';
      const close = () => { dialog.close(); dialog.remove(); button.focus(); };
      cancel.onclick = close;
      dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
      ok.onclick = () => {
        try { if(action) action(); notice=action ? 'Перевірено SSID/PSK чернетки в '+modeLabel+'. На роутер нічого не передано.' : 'Чернетку переглянуто. Повна перевірка цих параметрів у '+modeLabel+' недоступна.'; close(); render(); }
        catch (_) { close(); const error = form.querySelector('[role=alert]'); error.textContent='Перевірте SSID (1–32 байти) та пароль WPA (8–63 байти або 64 шістнадцяткові символи).'; error.focus(); }
      };
      dialog.append(cancel,ok); document.body.append(dialog); dialog.showModal(); cancel.focus();
    });
  }
  function render24General(panel) {
    const bands=element('nav',undefined,'wifi-tabs'); bands.setAttribute('aria-label','Діапазон Wi-Fi');
    bands.append(nav('2,4 ГГц','wifi/split/24/general',true),nav('5 ГГц','wifi/split/5/general',false)); panel.append(bands);
    const tabs=element('nav',undefined,'wifi-tabs wifi-section-tabs'); tabs.setAttribute('aria-label','Налаштування 2,4 ГГц');
    for(const [id,title] of Object.entries(WifiDemo.sections)) tabs.append(nav(title,'wifi/split/24/'+id,id==='general'));
    panel.append(tabs);
    const v=configuration?.bands['24'];
    const card=(title)=>{ const section=element('section',undefined,'wifi-general-card'); section.append(element('h2',title)); panel.append(section); return section; };
    const read=(section,label,value,kind='text')=>{
      const row=element('label',undefined,'wifi-field'); row.append(element('span',label));
      if(kind==='checkbox' && value!=='0' && value!=='1') {
        row.append(element('span','Невідомо')); section.append(row); return;
      }
      const input=element('input'); input.type=kind; input.disabled=true;
      if(kind==='checkbox') {input.checked=value==='1'; input.setAttribute('role','switch');}
      else input.value=value || 'Не задано';
      row.append(input); section.append(row);
    };
    const heading=card('Основна мережа 2,4 ГГц');
    heading.append(element('p','Показані збережені налаштування. Фактичний стан мережі перевіряється окремо.','wifi-note'));
    if(!v) {
      heading.append(element('p','Не вдалося прочитати конфігурацію. Оновіть сторінку або перейдіть до Classic.','wifi-load-error'));
    } else {
      read(heading,'Увімкнути радіомодуль 2,4 ГГц',v.radio_x,'checkbox');
      const identity=card('Назва мережі');
      if(configuration.shared==='1') {
        const note=element('div',undefined,'wifi-shared-lock');
        note.append(element('span','Назва та захист спільні для 2,4 і 5 ГГц'),nav('Редагувати у Спільних','wifi/common',false)); identity.append(note);
      }
      read(identity,'Назва мережі (SSID)',v.ssid);
      identity.append(element('p',new TextEncoder().encode(v.ssid).length+' / 32 байти UTF-8','wifi-byte-count'));
      read(identity,'Приховати SSID',v.closed,'checkbox');
      const radio=card('Радіопараметри');
      read(radio,'Режим мережі',{'2':'b/g/n','1':'b/g','5':'g/n','3':'Лише n','4':'Лише g','0':'Лише b'}[v.gmode] || 'Невідомий збережений режим');
      const usesHT=['2','3','5'].includes(v.gmode);
      if(usesHT) read(radio,'Ширина каналу',{'0':'20 МГц','1':'20/40 МГц'}[v.HT_BW] || 'Невідомо');
      read(radio,'Канал',v.channel==='0'?'Автоматично':v.channel);
      if(usesHT && v.HT_BW==='1') read(radio,'Додатковий канал',{'0':'Нижче','1':'Вище'}[v.HT_EXTCHA] || 'Невідомо');
      const security=card('Захист основної мережі');
      if(v.auth_mode==='open' && v.wep_x==='0') security.append(element('p','Мережа без пароля: дані не захищені шифруванням Wi-Fi.','wifi-open-warning'));
      else if(v.auth_mode==='psk' && v.wep_x==='0') {
        read(security,'Метод захисту','WPA Personal');
        read(security,'Версія WPA',{'0':'WPA / WPA2','1':'WPA','2':'WPA2'}[v.wpa_mode] || 'Невідомо');
        read(security,'Шифрування',{'aes':'AES','tkip':'TKIP','tkip+aes':'TKIP + AES'}[v.crypto] || 'Інше збережене шифрування');
        security.append(element('p','Пароль не завантажується. Збереження або зміна пароля в Modern ще розробляється.','wifi-note'));
      } else security.append(element('p','Збережено інший режим захисту. Його не буде автоматично змінено; налаштування доступні у Classic.','wifi-note'));
    }
    const advanced=card('Професійні налаштування');
    advanced.append(element('p','Розклад, потужність, пороги сигналу та додаткові параметри доступні у вкладці Професійні.','wifi-note'),nav('Професійні','wifi/split/24/advanced',false));
    const footer=element('div',undefined,'wifi-classic-actions');
    footer.append(element('span','Збереження в Modern ще розробляється','wifi-pending-label'));
    const classic=element('a','Перейти до Classic','wifi-tab'); classic.href='/Advanced_Wireless2g_Content.asp'; footer.append(classic); panel.append(footer);
  }
  function render24Guest(panel) {
    const bands=element('nav',undefined,'wifi-tabs');bands.setAttribute('aria-label','Діапазон Wi-Fi');
    bands.append(nav('2,4 ГГц','wifi/split/24/guest',true),nav('5 ГГц','wifi/split/5/guest',false));panel.append(bands);
    const tabs=element('nav',undefined,'wifi-tabs wifi-section-tabs');
    tabs.setAttribute('aria-label','Налаштування 2,4 ГГц');
    for(const [id,title] of Object.entries(WifiDemo.sections)) tabs.append(nav(title,'wifi/split/24/'+id,id==='guest'));
    panel.append(tabs);
    const grid=element('div',undefined,'wifi-guest-grid');
    const identityColumn=element('div',undefined,'wifi-guest-column');
    const accessColumn=element('div',undefined,'wifi-guest-column');
    grid.append(identityColumn,accessColumn);panel.append(grid);
    const card=(title,column=identityColumn)=>{const section=element('section',undefined,'wifi-general-card');section.append(element('h2',title));column.append(section);return section;};
    const read=(section,label,value,toggle=false)=>{
      const row=element('label',undefined,'wifi-field');row.append(element('span',label));
      if(value===null || value===undefined || (toggle && !['0','1'].includes(value))) row.append(element('span','Невідомо'));
      else {const input=element('input');input.disabled=true;input.type=toggle?'checkbox':'text';
        if(toggle){input.checked=value==='1';input.setAttribute('role','switch');} else input.value=value;
        row.append(input);}
      section.append(row);
    };
    const heading=card('Гостьова мережа 2,4 ГГц');
    heading.append(element('p','Показані збережені налаштування; фактичний стан перевіряється окремо.','wifi-note'));
    const v=configuration?.guests?.['24'];
    if(!v) heading.append(element('p','Не вдалося прочитати налаштування Guest. Оновіть сторінку або перейдіть до Classic.','wifi-load-error'));
    else {
      read(heading,'Увімкнути гостьову мережу',v.enable,true);
      if(configuration.bands['24'].radio_x==='0') heading.append(element('p','Радіомодуль 2,4 ГГц вимкнено. Гостьова мережа не може працювати без нього.','wifi-note'));
      const identity=card('Назва гостьової мережі');
      read(identity,'Назва мережі (SSID)',v.ssid);read(identity,'Приховати SSID',v.closed,true);
      const security=card('Захист');
      read(security,'Захист',v.auth_mode==='open'?'Відкрита мережа':v.auth_mode==='psk'?'WPA Personal':null);
      if(v.auth_mode==='open') security.append(element('p','Гостьова мережа без пароля: трафік Wi-Fi не захищений шифруванням.','wifi-open-warning'));
      if(v.auth_mode==='psk') {
        read(security,'Версія WPA',({'1':'WPA','2':'WPA2','0':'WPA + WPA2'})[v.wpa_mode]);
        read(security,'Шифрування',({aes:'AES',tkip:'TKIP','tkip+aes':'TKIP + AES'})[v.crypto]);
        security.append(element('p','Пароль залишається без змін. Збережений ключ не завантажується.','wifi-note'));
      }
      const isolation=card('Ізоляція та доступ',accessColumn);
      read(isolation,'Ізолювати від локальної мережі (LAN)',v.lan_isolate,true);
      read(isolation,'Ізолювати гостьових клієнтів між собою',v.ap_isolate,true);
      read(isolation,'Використовувати фільтр MAC-адрес',v.macrule,true);
      isolation.append(element('p','Фактичну ізоляцію необхідно перевірити на пристрої.','wifi-note'),nav('Налаштувати фільтр MAC','wifi/split/24/mac',false));
      const schedule=card('Розклад гостьової мережі',accessColumn);
      schedule.append(element('p','Час роутера використовується для розкладу.','wifi-note'));
      const decoded=WifiDemo.guestSchedule(v.date_x,v.time_x,v.time2_x);
      for(const [day,label] of [['mon','Пн'],['tue','Вт'],['wed','Ср'],['thu','Чт'],['fri','Пт'],['sat','Сб'],['sun','Нд']])
        read(schedule,label,decoded.days?(decoded.days[day]?'1':'0'):null,true);
      for(const [key,title] of [['weekday','Будні'],['weekend','Вихідні']]) read(schedule,title,decoded[key]?decoded[key].start+' – '+decoded[key].end:null);
      const extra=card('Додатково',accessColumn);
      const rates={'0':'Без фіксації','1':'HTMIX (1S) 45 Mbps','2':'HTMIX (1S) 30 Mbps','3':'HTMIX (1S) 15 Mbps','4':'OFDM 12 Mbps','5':'OFDM 9 Mbps','6':'OFDM 6 Mbps','7':'CCK 5.5 Mbps','8':'CCK 2 Mbps','9':'CCK 1 Mbps'};
      read(extra,'Фіксована швидкість передавання',rates[v.mcs_mode]);
    }
    const footer=element('div',undefined,'wifi-classic-actions');
    footer.append(element('span','Збереження в Modern ще розробляється','wifi-pending-label'));
    const classic=element('a','Перейти до Classic','wifi-tab');classic.href='/Advanced_WGuest2g_Content.asp';footer.append(classic);panel.append(footer);
  }
  function render() {
    const current = WifiDemo.route(location.hash);
    if (current.view === 'external') return;
    const visible = current.view !== 'home';
    home.hidden=visible; root.hidden=!visible;
    for (const [button, active] of [[homeButton,!visible],[wifiButton,visible]]) {
      button.classList.toggle('active',active);
      if (active) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current');
    }
    root.replaceChildren(); if (!visible) return;
    const back = nav('← Головна', '', false); root.append(back);
    const panel=element('section',undefined,'panel wifi-panel'); root.append(panel);
    const heading=element('div',undefined,'panel-heading');
    heading.append(element('h1','Бездротова мережа')); panel.append(heading);
    const tabs=element('nav',undefined,'wifi-tabs'); tabs.setAttribute('aria-label','Розділи Wi-Fi');
    tabs.append(nav('Спільні','wifi/common',current.view==='common'),nav('Розділені','wifi/split',['split','band'].includes(current.view)),nav('IoT 2,4 ГГц','wifi/iot',current.view==='iot')); panel.append(tabs);
    panel.append(element('p',schema.demo ? 'DEMO • Чернетки зберігаються до перезавантаження сторінки. Перехід між вкладками не застосовує налаштувань.' : 'READ-ONLY • Налаштування Wi-Fi доступні у Padavan Classic.','wifi-note'));
    if (notice) { const status=element('p',notice,'wifi-note'); status.setAttribute('role','status'); panel.append(status); }
    if (current.view==='split') {
      const cards=element('div',undefined,'wifi-band-links');
      for (const band of ['24','5']) cards.append(nav('Wi-Fi '+(band==='24'?'2,4':'5')+' ГГц →','wifi/split/'+band+'/general',false));
      panel.append(cards,element('p','Професійні параметри кожного діапазону доступні також при спільних SSID і паролі.','wifi-note')); return;
    }
    if (current.view==='iot') {
      panel.append(element('h2','IoT — у розробці','wifi-subheading'),
        element('p','Тут буде окрема мережа IoT лише для 2,4 ГГц. Налаштування SSID, захисту, підмережі, DHCP/DNS та ізоляції з’являться після готовності керування.','wifi-note'),
        element('p','Увімкнення та зміна налаштувань IoT наразі недоступні.','wifi-note'));
      return;
    }
    if (!schema.demo && current.view==='band' && current.band==='24' && current.section==='guest') {
      render24Guest(panel); return;
    }
    if (!schema.demo && current.view==='band' && current.band==='24' && current.section==='general') {
      render24General(panel); return;
    }
    if (!schema.demo) {
      panel.append(element('p','Збережені основні параметри доступні нижче. Зміна налаштувань Wi-Fi поки виконується у Classic.','wifi-note'));
      const bands=current.view==='band' ? [current.band] : ['24','5'];
      if(current.view==='common') {
        const summary=element('section',undefined,'wifi-shared-summary');
        summary.append(element('span','↔','wifi-shared-mark'),element('h2','Одна назва й захист для двох діапазонів'));
        summary.append(element('p','Канали, ширина, розклад, гостьові мережі та ввімкнення кожного радіомодуля налаштовуються окремо.'));
        summary.append(element('span',configuration?.shared==='1'?'Збережено: спільні':configuration?.shared==='0'?'Збережено: окремі':'Стан не отримано','wifi-stored-mode'));
        panel.append(summary);
      }

      if(current.view==='common' || current.section==='general') {
        panel.append(element('p','Збережені значення NVRAM. Фактичний стан радіо та застосування цих параметрів тут не перевіряються. Паролі не завантажуються.','wifi-note'));
        if(!configuration) panel.append(element('p','Не вдалося отримати поточну конфігурацію Wi-Fi. Скористайтеся Classic або оновіть сторінку.','wifi-note'));
        else {
          const cards=element('div',undefined,'wifi-saved-grid');
          for(const band of bands) {
          const card=element('section',undefined,'wifi-saved-card wifi-saved-'+band);
          card.append(element('span',band==='24'?'2.4 GHz':'5 GHz','wifi-band-mark'),element('h2','Збережено: '+(band==='24'?'2,4':'5')+' ГГц'));
          const values=configuration.bands[band];
          const list=element('dl',undefined,'wifi-stored-values');
          const security=values.auth_mode==='open' && values.wep_x==='0'?'Відкрита мережа':values.auth_mode==='psk' && values.wep_x==='0'?({'0':'WPA / WPA2 Personal','1':'WPA Personal','2':'WPA2 Personal'}[values.wpa_mode] || 'Інший збережений захист'):'Інший збережений захист';
          const radio=values.radio_x==='1'?'Увімкнено (збережено)':values.radio_x==='0'?'Вимкнено (збережено)':'Невідомо';
          const rows=[['SSID',values.ssid || 'Не задано'],['Захист',security],['Радіо',radio]];
          if(current.view!=='common') rows.push(['Канал',values.channel==='0'?'Автоматично':values.channel || 'Не задано']);
          for(const [label,value] of rows) list.append(element('dt',label),element('dd',value));
          card.append(list); cards.append(card);
          }
          panel.append(cards);
        }
      }
      if(current.view==='common') {
        const pending=element('section',undefined,'wifi-apply-pending');
        pending.append(element('h2','Спільна назва й захист'),element('p','Збереження в Modern ще розробляється. Для зміни назви, захисту або пароля скористайтеся Classic.','wifi-note'));
        panel.append(pending);
      }
      const actions=element('div',undefined,'wifi-classic-actions');
      for (const band of bands) {
        const section=current.view==='band' ? current.section : 'general';
        const page=schema.pages[band][section];
        if (!/^Advanced_[A-Za-z0-9_]+\.asp$/.test(page.classic)) throw Error('Invalid Classic destination');
        const link=element('a','Відкрити Classic: Wi-Fi '+(band==='24'?'2,4':'5')+' ГГц — '+WifiDemo.sections[section],'wifi-tab');
        link.href='/'+page.classic; actions.append(link);
      }
      panel.append(actions);
      return;
    }
    const form=element('form',undefined,'wifi-settings'); form.autocomplete='off';
    const error=element('p','','wifi-error'); error.setAttribute('role','alert'); error.tabIndex=-1; form.append(error);
    let action=null;
    if (current.view==='common') {
      panel.append(element('p','Спільний механізм переносить лише SSID, автентифікацію, шифрування та пароль. Увімкнення радіо й приховування SSID задаються окремо для діапазонів.','wifi-note'));
      field(form,state,'shared','Спільні SSID та захист для 2,4 + 5 ГГц',null,'checkbox');
      // Boolean selector is deliberately independent of navigation and draft editing.
      const selector=form.querySelector('[name=shared]'); selector.checked=state.shared===true;
      selector.addEventListener('input',()=>{state.shared=selector.checked;});
      basic(form,state.common,true);
      action=()=>{ if(state.shared) WifiDemo.synchronize(state,window.WRSharedWifi.plan); };
    } else {
      const band=current.band; const prefix=band==='24'?'rt_':'wl_';
      panel.append(nav('← Вибір діапазону','wifi/split',false),element('h2','Wi-Fi '+(band==='24'?'2,4':'5')+' ГГц','wifi-subheading'));
      const subnav=element('nav',undefined,'wifi-tabs'); subnav.setAttribute('aria-label','Налаштування діапазону');
      for (const [id,title] of Object.entries(WifiDemo.sections)) subnav.append(nav(title,'wifi/split/'+band+'/'+id,current.section===id)); panel.append(subnav);
      panel.append(element('p','Інвентар полів Classic, а не підтвердження роботи кожної функції. Успадковані опції без перевірки драйвера не вважаються підтримуваними. Beamforming для WR1200JS вилучено.','wifi-note'));
      const page=schema.pages[band][current.section];
      panel.append(element('p','Classic: '+page.classic,'wifi-source'));
      let fields=page.fields;
      const advanced = f => /_(radio_(date|time)|TxPower|KickStaRssiLow|AssocReqRssiThres|mcs_mode|gmode_protection|wpa_gtk_rekey)/.test(f.key);
      if(current.section==='general') fields=fields.filter(f=>!advanced(f));
      if(current.section==='advanced') fields=[...fields,...schema.pages[band].general.fields.filter(advanced)];
      if(current.section==='general') {
        basic(form,state.bands[band]);
        if(state.shared) for (const control of form.querySelectorAll('input,select')) if (WifiDemo.commonKeys.includes(control.name)) control.disabled=true;
        fields=fields.filter(f=>!['radio_x','ssid','closed','auth_mode','crypto','wpa_psk','wep_x','key','key1','key2','key3','key4','phrase_x'].includes(f.key.slice(prefix.length)));
      }
      for (const f of fields) {
        const key=f.key.slice(prefix.length);
        const locked=state.shared && WifiDemo.commonKeys.includes(key);
        field(form,state.bands[band],key,f.label,f.options,f.type,locked,f.maxLength);
      }
      if(state.shared) panel.append(element('p','Спільний режим: SSID та захист редагуються у «Спільні». Інші параметри залишаються незалежними.','wifi-note'));
      if(current.section==='general') panel.append(element('p','Цей етап моделює відкриту мережу та WPA Personal. Залежності Enterprise/WEP, списки MAC/WDS й динамічні обмеження каналів ще не перенесені з Classic; реальне застосування заблоковане.','wifi-note'));
      if(current.section==='general') action=()=>window.WRSharedWifi.plan('0','1',band==='24'?'rt':'wl',state.bands[band]);
    }
    confirmDraft(form,action); panel.append(form);
  }
  wifiButton.onclick=()=>go('wifi/common'); homeButton.onclick=()=>go('');
  window.addEventListener('hashchange',render); render();
})().catch(error => {
  console.error(error);
  const target=document.getElementById('modern-wifi');
  target.hidden=false; target.textContent='Не вдалося завантажити структуру Wi-Fi. Оновіть локальний preview.';
});
