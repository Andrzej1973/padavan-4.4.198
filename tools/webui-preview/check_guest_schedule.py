#!/usr/bin/env python3
"""Compare Modern schedule decoding to pinned Classic functions, without extraction."""
import json
import pathlib
import subprocess
import sys
import tarfile

archive = pathlib.Path(sys.argv[1])
with tarfile.open(archive) as source:
    text = source.extractfile('trunk/user/www/n56u_ribbon_fixed/general.js').read().decode()
start = text.index('function getDateCheck(')
end = text.index('function setDateCheck(', start)
classic = text[start:end]
module = pathlib.Path(__file__).resolve().parent / 'public/wifi.js'
program = '''
const assert=require('node:assert/strict');
const vm=require('node:vm');
const modern=require(MODULE);
const classic={};vm.createContext(classic);vm.runInContext(CLASSIC,classic);
for(let mask=0;mask<128;mask++) {
 const date=mask.toString(2).padStart(7,'0');
 const got=modern.guestSchedule(date,'08002200','10002359');
 ['sun','mon','tue','wed','thu','fri','sat'].forEach((day,i)=>assert.equal(got.days[day],classic.getDateCheck(date,i)));
}
for(let h=0;h<24;h++) for(let m=0;m<60;m++) {
 const date=String(h).padStart(2,'0')+String(m).padStart(2,'0')+'2359';
 const got=modern.guestSchedule('0000000',date,date);
 const expected={start:classic.getTimeRange(date,0)+':'+classic.getTimeRange(date,1),end:classic.getTimeRange(date,2)+':'+classic.getTimeRange(date,3)};
 assert.deepEqual(got.weekday,expected);assert.deepEqual(got.weekend,expected);
}
for(const bad of [null,undefined,7,'','111111','11111111','101x010',' 111111']) assert.equal(modern.guestSchedule(bad,'00002359','00002359').days,null);
for(const bad of [null,undefined,7,'','0800220','24002200','08602200','08002400','08002260','abcdefgh',' 08002200']) {
 const got=modern.guestSchedule('1111111',bad,bad);
 assert.equal(got.weekday,null);assert.equal(got.weekend,null);
}
// Stored equal and overnight ranges are displayed faithfully; this decoder
// does not establish RC scheduling semantics or authorize persistence.
assert.deepEqual(modern.guestSchedule('0000000','22000800','08000800').weekday,{start:'22:00',end:'08:00'});
assert.deepEqual(modern.guestSchedule('0000000','22000800','08000800').weekend,{start:'08:00',end:'08:00'});
console.log('PASS Guest stored schedule: 128 day masks and 1440 times match actual Classic; invalid values unknown; no apply/runtime claim');
'''.replace('MODULE', json.dumps(str(module))).replace('CLASSIC', json.dumps(classic))
subprocess.run(['node', '-'], input=program, text=True, check=True)
