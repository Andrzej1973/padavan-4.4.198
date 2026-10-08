/* Explicit refresh only; cached observations are never presented as fresh. */
function wrBandRefresh() {
 var button = document.getElementById('wr_bs_refresh');
 var label = document.getElementById('wr_bs_status');
 if (!button || !label || button.disabled) return;
 var oldSerial, attempts = 0;
 button.disabled = true;
 label.textContent = label.getAttribute('data-wait');
 function finish(key) {
  label.textContent = label.getAttribute('data-' + key);
  button.disabled = false;
 }
 function valid(data) {
  return data && typeof data.serial === 'number' && data.serial >= 0 &&
   data.serial % 1 === 0 && data.serial <= 2147483647 &&
   (data.observation === 0 || data.observation === 1 || data.observation === 2);
 }
 function poll() {
  $j.ajax({url: '/update.cgi', data: {output: 'wr_band_observation'},
   dataType: 'json', cache: false, timeout: 3000,
   success: function(data) {
    if (!valid(data)) return finish('unknown');
    if (data.serial > 0 && data.serial !== oldSerial)
     return finish(data.observation === 1 ? 'active' : data.observation === 2 ? 'off' : 'unknown');
    if (++attempts >= 6) return finish('unknown');
    setTimeout(poll, 1000);
   }, error: function() { finish('unknown'); }
  });
 }
 $j.ajax({url: '/update.cgi', type: 'POST',
  data: {output: 'wr_band_observation', arg0: 'refresh'},
  dataType: 'json', cache: false, timeout: 3000,
  success: function(data) {
   if (!valid(data)) return finish('unknown');
   oldSerial = data.serial;
   setTimeout(poll, 1000);
  }, error: function() { finish('unknown'); }
 });
}
