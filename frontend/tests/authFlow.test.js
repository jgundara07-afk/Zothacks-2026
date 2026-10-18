import test from 'node:test';
import assert from 'node:assert/strict';
import {register,login,startGoogleSignIn,resendVerification,logout} from '../src/authFlow.js';

const payload={name:'  Sam  ',email:' Sam@GMAIL.COM ',password:'long-enough-password',confirmation:'long-enough-password',redirectTo:'http://127.0.0.1:5173'};

test('signup sends normalized email and name and waits for verification',async()=>{
 let sent;
 const client={auth:{signUp:async data=>{sent=data;return {data:{user:{identities:[{id:'1'}]},session:null}}}}};
 assert.match(await register(payload,client),/verification link/);
 assert.equal(sent.email,'Sam@gmail.com');
 assert.equal(sent.options.data.name,'Sam');
 assert.equal(sent.options.emailRedirectTo,payload.redirectTo);
});
test('duplicate signup is handled without claiming success',async()=>{
 const client={auth:{signUp:async()=>({data:{user:{identities:[]},session:null}})}};
 assert.match(await register(payload,client),/already has an account/);
});
test('invalid signup inputs never reach the provider',async()=>{
 const client={auth:{signUp:async()=>{throw new Error('should not be called')}}};
 await assert.rejects(register({...payload,email:'x@other.edu'},client),/Gmail/);
 await assert.rejects(register({...payload,email:'broken'},client),/valid email/);
 await assert.rejects(register({...payload,confirmation:'different'},client),/do not match/);
});
test('incorrect password and unverified email give clear login errors',async()=>{
 for(const [code,expected] of [['invalid_credentials',/incorrect/],['email_not_confirmed',/Verify your email/]]){
  const client={auth:{signInWithPassword:async()=>({error:{code}})}};
  await assert.rejects(login(payload,client),expected);
 }
});
test('signup distinguishes email delivery limits from request limits',async()=>{
 for(const [code,expected] of [
  ['over_email_send_rate_limit',/Verification emails are temporarily limited/],
  ['over_request_rate_limit',/Too many requests from this network/],
  ['email_address_not_authorized',/Email delivery needs to be configured/],
 ]){
  const client={auth:{signUp:async()=>({error:{code}})}};
  await assert.rejects(register(payload,client),error=>{
   assert.equal(error.code,code);
   assert.match(error.message,expected);
   return true;
  });
 }
});
test('login returns verified provider session and rejects absent session',async()=>{
 const session={access_token:'token',user:{id:'user-id'}};
 let sent;
 const client={auth:{signInWithPassword:async data=>{sent=data;return {data:{session}}}}};
 assert.equal(await login(payload,client),session);
 assert.deepEqual(sent,{email:'Sam@gmail.com',password:payload.password});
 await assert.rejects(login(payload,{auth:{signInWithPassword:async()=>({data:{session:null}})}}),/verify your session/);
});
test('Google sign-in starts Supabase OAuth with the current app URL',async()=>{
 let sent;
 const client={auth:{signInWithOAuth:async data=>{sent=data;return {data:{url:'https://example.test/authorize'}}}}};
 assert.equal(await startGoogleSignIn({redirectTo:'http://127.0.0.1:5173/'},client),'https://example.test/authorize');
 assert.deepEqual(sent,{provider:'google',options:{redirectTo:'http://127.0.0.1:5173/'}});
 await assert.rejects(startGoogleSignIn({redirectTo:'http://127.0.0.1:5173/'},{auth:{signInWithOAuth:async()=>({error:{message:'Provider disabled'}})}}),/Provider disabled/);
});
test('signup cannot create an active session when email confirmation is off',async()=>{
 let signedOut=false;
 const client={auth:{signUp:async()=>({data:{session:{access_token:'token'}}}),signOut:async()=>{signedOut=true}}};
 await assert.rejects(register(payload,client),/Email verification must be enabled/);
 assert.equal(signedOut,true);
});

test('resending verification uses the normalized address without leaking account existence',async()=>{
 let sent;
 const client={auth:{resend:async data=>{sent=data;return {error:null}}}};
 assert.match(await resendVerification({email:' Sam@GMAIL.COM ',redirectTo:payload.redirectTo},client),/If Sam@gmail.com has an unverified account/);
 assert.deepEqual(sent,{type:'signup',email:'Sam@gmail.com',options:{emailRedirectTo:payload.redirectTo}});
});

test('logout calls the provider and reports a failed sign-out',async()=>{
 let called=0;
 await logout({auth:{signOut:async()=>{called++;return {error:null}}}});
 assert.equal(called,1);
 await assert.rejects(logout({auth:{signOut:async()=>({error:{message:'Could not sign out'}})}}),/Could not sign out/);
});
