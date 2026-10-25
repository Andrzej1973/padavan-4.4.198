"use strict";

// Demo drafts only. No storage, CGI, NVRAM writes, or router requests.
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
    if (parts[0] !== 'wifi') return {view:'home'};
    if (parts[1] === 'split' && ['24','5'].includes(parts[2])) return {view:'band', band:parts[2], section:Object.hasOwn(sections, parts[3]) ? parts[3] : 'general'};
    return {view:['common','split','iot'].includes(parts[1]) ? parts[1] : 'common'};
  }
  return {commonKeys, sections, makeState, synchronize, route};
})();
if (typeof module !== 'undefined') module.exports = WifiDemo;

if (typeof document !== 'undefined') (async () => {
  const response = await fetch('/wifi-schema.json', {credentials:'omit', cache:'no-store'});
  if (!response.ok) throw Error('Wi-Fi schema unavailable');
  const schema = await response.json();
  if (schema.demo !== true) throw Error('Unmarked Wi-Fi schema');
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
    const button = element('button',action ? 'Перевірити й застосувати в DEMO' : 'Переглянути чернетку DEMO','primary-button');
    button.type='submit'; form.append(button);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const dialog = element('dialog', undefined, 'wifi-confirm');
      dialog.setAttribute('aria-label','Попередження перед застосуванням');
      dialog.append(element('h2','Зміни Wi-Fi можуть розірвати з’єднання'),element('p','Це лише локальне DEMO. Підтвердження перевіряє чернетку в пам’яті; роутер не змінюється.'));
      const cancel = element('button','Назад до редагування','wifi-tab'); cancel.type='button';
      const ok = element('button','Підтвердити DEMO','primary-button'); ok.type='button';
      const close = () => { dialog.close(); dialog.remove(); button.focus(); };
      cancel.onclick = close;
      dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
      ok.onclick = () => {
        try { if(action) action(); notice=action ? 'Перевірено SSID/PSK чернетки в DEMO. На роутер нічого не передано.' : 'Чернетку переглянуто. Повна перевірка цих параметрів у DEMO недоступна.'; close(); render(); }
        catch (_) { close(); const error = form.querySelector('[role=alert]'); error.textContent='Перевірте SSID (1–32 байти) та пароль WPA (8–63 байти або 64 шістнадцяткові символи).'; error.focus(); }
      };
      dialog.append(cancel,ok); document.body.append(dialog); dialog.showModal(); cancel.focus();
    });
  }
  function render() {
    const current = WifiDemo.route(location.hash);
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
    panel.append(element('p','DEMO • Чернетки зберігаються до перезавантаження сторінки. Перехід між вкладками не застосовує налаштувань.','wifi-note'));
    if (notice) { const status=element('p',notice,'wifi-note'); status.setAttribute('role','status'); panel.append(status); }
    if (current.view==='split') {
      const cards=element('div',undefined,'wifi-band-links');
      for (const band of ['24','5']) cards.append(nav('Wi-Fi '+(band==='24'?'2,4':'5')+' ГГц →','wifi/split/'+band+'/general',false));
      panel.append(cards,element('p','Професійні параметри кожного діапазону доступні також при спільних SSID і паролі.','wifi-note')); return;
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
    } else if (current.view==='iot') {
      panel.append(element('p','IoT: макет окремої мережі. Додатковий BSS підтверджений на рівні джерел; активація ra2, окремий DHCP та firewall у виробничому образі й на роутері не прийняті. Перемикачі ізоляції — лише проєктні параметри.','wifi-note'));
      basic(form,state.iot);
      field(form,state.iot,'clientIsolation','Ізоляція клієнтів — не перевірено',null,'checkbox');
      field(form,state.iot,'lanIsolation','Ізоляція від основної LAN — не перевірено',null,'checkbox');
      action=()=>window.WRSharedWifi.plan('0','1','rt',state.iot);
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
