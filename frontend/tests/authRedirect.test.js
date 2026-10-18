import test from 'node:test';
import assert from 'node:assert/strict';
import {verificationRedirectError} from '../src/authRedirect.js';

test('successful or ordinary visits show no verification error',()=>{
  assert.equal(verificationRedirectError('http://127.0.0.1:5173/'), '');
  assert.equal(verificationRedirectError('http://127.0.0.1:5173/#access_token=example'), '');
});
test('expired and invalid links show safe, actionable errors',()=>{
  assert.match(verificationRedirectError('http://127.0.0.1:5173/#error=access_denied&error_code=otp_expired'),/expired/);
  assert.match(verificationRedirectError('http://127.0.0.1:5173/?error=access_denied&error_description=<script>'),/could not complete sign-in/);
});
