const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
// Regression: damaged local data must never be silently replaced by starter tasks.
function harness(initial,readError=false){
 const src=fs.readFileSync(path.join(__dirname,'../app.js'),'utf8');
 const start=src.indexOf('let state;'),end=src.indexOf('\nconst el=',start);
 assert.ok(start>=0&&end>start,'production load/persist block missing');
 let raw=initial,writes=0;
 const ctx={C:{sections:[],tasks:[]},M:{normalize:x=>x},KEY:'test',setTimeout:()=>0,notice:()=>{},localStorage:{
   getItem:()=>{if(readError)throw Error('disabled');return raw},
   setItem:(_k,v)=>{raw=v;writes++}
 }};
 const h=vm.runInNewContext('(()=>{'+src.slice(start,end)+';return {load,persist,setState:x=>{state=x},getFault:()=>storageFault,getRaw:()=>rawOnFailure}})()',ctx);
 return{h,stored:()=>raw,writes:()=>writes};
}
test('corrupted JSON survives startup intact',()=>{
 const x=harness('{broken');x.h.setState(x.h.load());
 assert.equal(x.h.getFault(),true);assert.equal(x.h.persist(),false);
 assert.equal(x.stored(),'{broken');assert.equal(x.writes(),0);
 assert.equal(x.h.getRaw(),'{broken');
});
test('invalid state structure is preserved for recovery',()=>{
 const x=harness('{"tasks":"invalid"}');x.h.setState(x.h.load());
 assert.equal(x.h.persist(),false);assert.equal(x.writes(),0);
});
test('valid JSON remains writable',()=>{
 const x=harness('{"sections":[],"tasks":[]}');x.h.setState(x.h.load());
 assert.equal(x.h.getFault(),false);assert.equal(x.h.persist(),true);assert.equal(x.writes(),1);
});
test('blank storage initializes on first use',()=>{
 const x=harness('');x.h.setState(x.h.load());
 assert.equal(x.h.getFault(),false);assert.equal(x.h.persist(),true);
});
test('unavailable storage does not trigger destructive writes',()=>{
 const x=harness('private',true);x.h.setState(x.h.load());
 assert.equal(x.h.getFault(),true);assert.equal(x.h.persist(),false);assert.equal(x.writes(),0);
});
