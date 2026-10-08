/* Local payload only. No network requests, storage, DOM output or logging. */
function wrWifiQrPayload(settings) {
 function bytes(value) { return unescape(encodeURIComponent(value)).length; }
 function escape(value) { return value.replace(/([\\;,:"])/g, '\\$1'); }
 if (!settings || typeof settings.ssid !== 'string' || !settings.ssid || /[\x00-\x1f\x7f]/.test(settings.ssid))
  return {error: 'ssid'};
 try { if (bytes(settings.ssid) > 32) return {error: 'ssid'}; }
 catch (error) { return {error: 'encoding'}; }
 var type, password = '';
 if (settings.auth === 'open' && String(settings.wep) === '0') type = 'nopass';
 else if (settings.auth === 'psk') {
  type = 'WPA';
  if (typeof settings.password !== 'string') return {error: 'password'};
  password = settings.password;
  if (/[\x00-\x1f\x7f]/.test(password)) return {error: 'password'};
  try {
   var length = bytes(password);
   // Raw 64-digit PSKs require separate phone interoperability verification.
   if (length < 8 || length > 63) return {error: 'password'};
  } catch (error) { return {error: 'encoding'}; }
 } else return {error: 'security'};
 var hidden = settings.hidden === true || settings.hidden === 1 || settings.hidden === '1';
 return {payload: 'WIFI:T:' + type + ';S:' + escape(settings.ssid) +
  (type === 'nopass' ? '' : ';P:' + escape(password)) + ';H:' + (hidden ? 'true' : 'false') + ';;'};
}
if (typeof module !== 'undefined') module.exports = wrWifiQrPayload;
