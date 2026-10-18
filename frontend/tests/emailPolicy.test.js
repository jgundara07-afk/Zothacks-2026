import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeEmail} from '../src/emailPolicy.js';

test('accepts all supported domains and normalizes surrounding space and domain case', () => {
 for (const domain of ['gmail.com','outlook.com','hotmail.com','live.com','yahoo.com','icloud.com','me.com','mac.com','proton.me','protonmail.com','uci.edu']) {
  assert.equal(normalizeEmail(`  Person+tag@${domain.toUpperCase()}  `), `Person+tag@${domain}`);
 }
});

test('rejects unsupported and malformed addresses', () => {
 for (const email of ['a@other.edu','a@gmail.com.evil','a@@gmail.com','a@gmail.com extra','a@-gmail.com','.a@gmail.com','a..b@gmail.com','not-an-email','']) {
  assert.throws(() => normalizeEmail(email), /valid email|Gmail/);
 }
});
