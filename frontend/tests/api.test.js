import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createApiClient} from '../src/api.js';
const api=createApiClient(async()=>({data:{session:{access_token:'test-token'}}}));

test('empty proxy gateway errors report a backend connection failure',async t=>{
 const original=globalThis.fetch;t.after(()=>{globalThis.fetch=original});
 for(const status of [502,503,504]){
  globalThis.fetch=async()=>new Response('',{status});
  await assert.rejects(api.progress(),/Cannot reach One Thing/);
 }
});
test('JSON service errors retain their useful message and valid responses still load',async t=>{
 const original=globalThis.fetch;t.after(()=>{globalThis.fetch=original});
 globalThis.fetch=async()=>new Response(JSON.stringify({error:'Storage is unavailable. Please try again.'}),{status:503});
 await assert.rejects(api.progress(),/Storage is unavailable/);
 globalThis.fetch=async()=>new Response(JSON.stringify({points:125}),{status:200});
 assert.equal((await api.progress()).points,125);
});
