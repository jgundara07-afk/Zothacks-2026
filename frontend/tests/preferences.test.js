import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {toggleSelection} from '../src/utils/preferences.js';
import {chooseVariant,matchesOpportunity} from '../src/utils/filtering.js';
const options=JSON.parse(readFileSync(new URL('../../shared/preferences.json',import.meta.url)));

test('interests stop at ten and goals at three; deselection frees a slot',()=>{
 for(const field of ['interests','goals']){
  const limit=options[`max_selected_${field}`];assert.equal(limit,field==='interests'?10:3);
  let selected=[];
  for(const item of options[field].slice(0,limit+1))selected=toggleSelection(selected,item,limit);
  assert.deepEqual(selected,options[field].slice(0,limit));
  selected=toggleSelection(selected,options[field][1],limit);
  selected=toggleSelection(selected,options[field][limit],limit);
  assert.deepEqual(selected,[...options[field].slice(0,limit).filter(v=>v!==options[field][1]),options[field][limit]]);
 }
});

test('collected filters use catalog challenge/time independently of preparation steps',()=>{
 const raw=JSON.parse(readFileSync(new URL('../../backend/catalog/sample.json',import.meta.url))).opportunities.find(o=>o.personalization.filter_interests?.length&&o.difficulty!=='Lazy');
 const p=raw.personalization;
 const o={...raw,topics:p.interests,career_goals:[],venues:p.location_preferences};
 const preferences={challenges:p.challenge_levels,time:p.time_buckets,locations:[],commitment:p.commitment};
 const q={id:'preparation',opportunity_id:o.id,daily:true,difficulty:'Lazy',minutes:2,time_bucket:'Under 5 min',effort:'small',size:'Small'};
 assert.ok(matchesOpportunity(o,{interests:p.interests,goals:[],preferences}));
 assert.equal(chooseVariant(o,[q],{stepSize:'Small',preferences,defaultEffort:'small'}),q);
 assert.equal(matchesOpportunity(o,{interests:[],goals:[],preferences:{...preferences,time:['Under 5 min']}}),false);
 assert.equal(matchesOpportunity(o,{interests:[],goals:[],preferences:{...preferences,challenges:['Lazy']}}),false);
});
