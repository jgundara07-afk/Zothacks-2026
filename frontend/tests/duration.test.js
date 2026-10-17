import {test} from 'node:test';
import assert from 'node:assert/strict';
import {durationLabel} from '../src/utils/duration.js';

test('full duration distinguishes source times, estimates and unknown totals',()=>{
 assert.equal(durationLabel({min_minutes:60,max_minutes:120,quality:'Source range'}),'60–120 min · Source range');
 assert.equal(durationLabel({min_minutes:60,max_minutes:60,quality:'Source reported'}),'60 min · Source reported');
 assert.equal(durationLabel({min_minutes:null,max_minutes:null,quality:'Unknown'}),'Total not provided · Unknown');
});
