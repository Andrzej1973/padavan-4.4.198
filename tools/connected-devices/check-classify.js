'use strict';
const assert=require('assert');
const classify=require('./classify.js').classify;
assert.strictEqual(classify({}).category,'Unknown');
assert.strictEqual(classify({hostname:'android-phone'}).confidence,'Possible');
assert.strictEqual(classify({hostname:'android-phone',vendorClass:'android-dhcp'}).confidence,'High');
assert.strictEqual(classify({hostname:'DESKTOP-test',vendorClass:'MSFT 5.0'}).category,'Windows');
const conflict=classify({hostname:'android-phone',vendorClass:'MSFT 5.0'});
assert.strictEqual(conflict.category,'Unknown');assert.strictEqual(conflict.os,'');
const apple=classify({mac:'00:11:22:33:44:55',ouiVendor:'Apple, Inc.'});
assert.strictEqual(apple.category,'Apple');assert.strictEqual(apple.os,'');assert.strictEqual(apple.confidence,'Manufacturer identified');
for(const mac of ['02:11:22:33:44:55','01:11:22:33:44:55','invalid']){
 const result=classify({mac:mac,ouiVendor:'Apple, Inc.'});assert.strictEqual(result.category,'Unknown');assert.strictEqual(result.manufacturer,'');
}
const tv=classify({hostname:'android-tv-livingroom',vendorClass:'Android'});
assert.strictEqual(tv.category,'Smart TV');assert.strictEqual(tv.os,'Android');assert.strictEqual(tv.formFactor,'TV');
assert.strictEqual(classify({hostname:'activity'}).category,'Unknown');
assert.strictEqual(classify({manualCategory:'Windows'}).confidence,'User specified');
assert.strictEqual(classify({manualCategory:'<script>'}).category,'Unknown');
const hostile='<img src=x onerror=alert(1)>';
assert.strictEqual(classify({hostname:hostile}).category,'Unknown');
assert.ok(classify({hostname:'x'.repeat(10000),ouiVendor:'x'.repeat(10000),mac:'00:11:22:33:44:55'}).manufacturer.length<=128);
console.log('PASS bounded device classification: conservative confidence, conflicting clues, random MACs, manufacturer/OS separation and TV form factor');
