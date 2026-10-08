const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, 'status-ui.js'), 'utf8');
function scenario(responses, expected, requestsExpected) {
 const button = {disabled: false};
 const label = {textContent: '', getAttribute: key => key};
 const timers = [], requests = [];
 const context = {document: {getElementById: id => id === 'wr_bs_refresh' ? button : label},
  setTimeout: (fn, ms) => {assert.equal(ms, 1000); timers.push(fn);},
  $j: {ajax: options => {
   requests.push(options);
   assert.equal(options.url, '/update.cgi');
   assert.equal(options.timeout, 3000);
   assert.equal(options.cache, false);
   const response = responses.shift();
   assert.notEqual(response, undefined, 'unexpected request');
   if (response === 'error') options.error(); else options.success(response);
  }}};
 vm.createContext(context); vm.runInContext(source, context);
 context.wrBandRefresh();
 // A repeated click while awaiting a result must not create another request.
 if (button.disabled) {const count=requests.length; context.wrBandRefresh(); assert.equal(requests.length,count);}
 let limit=10;
 while (timers.length && --limit) timers.shift()();
 assert.ok(limit > 0, 'polling must terminate');
 assert.equal(label.textContent, 'data-'+expected);
 assert.equal(button.disabled, false);
 assert.equal(requests.length, requestsExpected);
 assert.equal(requests[0].type, 'POST');
 assert.equal(requests[0].data.arg0, 'refresh');
 for (const request of requests.slice(1)) assert.equal(request.data.arg0, undefined);
}
const data = (serial, observation) => ({serial, observation});
scenario([data(4,0), data(5,1)], 'active', 2);
scenario([data(4,0), data(5,2)], 'off', 2);
scenario([data(4,1), data(5,0)], 'unknown', 2);
scenario([data(4,1), ...Array.from({length:6},()=>data(4,1))], 'unknown', 7);
scenario([data(2147483647,0), data(1,1)], 'active', 2);
scenario(['error'], 'unknown', 1);
scenario([data(4,1), 'error'], 'unknown', 2);
scenario([data('4',1)], 'unknown', 1);
scenario([data(4,1), data(5,99)], 'unknown', 2);
scenario([data(4,1), data(0,1), data(5,1)], 'active', 3);
console.log('PASS: 10 actual-JavaScript status scenarios; bounded polling, no duplicate refresh');
