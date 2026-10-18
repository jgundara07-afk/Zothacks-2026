import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveAuthConfiguration} from '../src/authConfiguration.js';
import {assertPublicSupabaseKey} from '../authKeySafety.js';

test('missing values leave auth disabled with a useful setup error',()=>{
  assert.match(resolveAuthConfiguration({}).error,/frontend\/\.env\.local/);
  assert.match(resolveAuthConfiguration({VITE_SUPABASE_URL:'https://example.supabase.co'}).error,/public key/);
});
test('publishable and legacy anon keys can configure the same project',()=>{
  const base={VITE_SUPABASE_URL:'https://example.supabase.co'};
  assert.equal(resolveAuthConfiguration({...base,VITE_SUPABASE_PUBLISHABLE_KEY:'sb_publishable_example'}).error,null);
  assert.equal(resolveAuthConfiguration({...base,VITE_SUPABASE_ANON_KEY:'legacy-anon'}).key,'legacy-anon');
});
test('invalid URLs and secret keys are rejected',()=>{
  assert.match(resolveAuthConfiguration({VITE_SUPABASE_URL:'javascript:bad',VITE_SUPABASE_PUBLISHABLE_KEY:'public'}).error,/invalid/);
  assert.match(resolveAuthConfiguration({VITE_SUPABASE_URL:'https://example.supabase.co',VITE_SUPABASE_PUBLISHABLE_KEY:'sb_secret_do-not-use'}).error,/secret key/);
  assert.throws(()=>assertPublicSupabaseKey('VITE_SUPABASE_ANON_KEY','sb_secret_do-not-use'),/secret\/service-role/);
});
