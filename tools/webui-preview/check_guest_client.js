'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {guestApplyResult,guestSubmission}=require('./public/wifi.js');
const reply={schemaVersion:1,state:'configuration_matches',settingsMayHaveChanged:true,ramConfigurationMatches:true,flashCommit:'requested_unverified',serviceNotification:'requested_unverified',runtimeVerified:false,automaticRetry:false,nextAction:'reload_configuration'};
(async()=>{
  assert.equal(guestApplyResult(reply).state,'configuration_matches');
  for(const invalid of [null,{},[],{...reply,runtimeVerified:true},{...reply,automaticRetry:true},{...reply,flashCommit:'confirmed'},{...reply,serviceNotification:'completed'},{...reply,state:'success'},{...reply,ramConfigurationMatches:false},{...reply,wpa_psk:'secret'},{...reply,schemaVersion:2},{...reply,settingsMayHaveChanged:false}])assert.equal(guestApplyResult(invalid).state,'unknown');
  for(const state of ['reload_required','busy','rejected','unconfirmed','unavailable']){
    const got=guestApplyResult({...reply,state,settingsMayHaveChanged:state==='unconfirmed',ramConfigurationMatches:false,flashCommit:'not_requested',serviceNotification:'not_requested'});
    assert.equal(got.state,state);assert.equal(got.automaticRetry,false);assert.equal(got.requiresReload,true);
  }
  let calls=0,complete;
  const submit=guestSubmission(async body=>{calls++;assert.equal(body,'private-body');return await new Promise(resolve=>{complete=resolve;});});
  const first=submit.submit('private-body');
  assert.equal(submit.getState().state,'pending');assert.equal(await submit.submit('second'),false);
  await new Promise(resolve=>setImmediate(resolve));assert.equal(calls,1);complete(reply);
  assert.equal((await first).state,'configuration_matches');assert.equal(await submit.submit('again'),false);assert.equal(calls,1);
  assert(!JSON.stringify(submit.getState()).includes('private-body'));
  const lost=guestSubmission(async body=>{calls++;throw Error('sensitive '+body);});
  assert.equal((await lost.submit('SECRET')).state,'unknown');assert.equal(await lost.submit('SECRET'),false);
  assert(!JSON.stringify(lost.getState()).includes('SECRET'));
  let late,signal;
  const timeout=guestSubmission((body,options)=>{calls++;signal=options.signal;return new Promise(resolve=>{late=resolve;});},{timeoutMs:2});
  assert.equal((await timeout.submit('private')).state,'unknown');assert.equal(signal.aborted,true);
  late(reply);await new Promise(resolve=>setImmediate(resolve));assert.equal(timeout.getState().state,'unknown');assert.equal(await timeout.submit('again'),false);
  if(process.argv.includes('--actual-replies')){
    const replies=JSON.parse(fs.readFileSync(0,'utf8'));assert.equal(replies.length,77);
    for(const value of replies){const got=guestApplyResult(value);assert.equal(got.state,value.state);assert.equal(got.runtimeVerified,false);assert.equal(got.automaticRetry,false);}
    console.log('PASS actual C JSON -> Modern client:77 replies agree; no radio/flash acceptance');
  }
  console.log('PASS Guest client: strict protocol, single pending/send, network loss/timeout unknown, late result ignored, no replay or secret in state; controller not production-bound');
})().catch(error=>{console.error(error);process.exitCode=1;});
