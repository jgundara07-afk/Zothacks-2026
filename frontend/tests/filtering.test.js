import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chooseVariant,matchesOpportunity} from '../src/utils/filtering.js';
const seed=JSON.parse(readFileSync(new URL('../../backend/seed.json',import.meta.url)));
const options=JSON.parse(readFileSync(new URL('../../shared/preferences.json',import.meta.url)));
const base={challenges:[],time:[],locations:[],commitment:'A mix of both'};
function matching(interests=[],goals=[],preferences=base){return seed.opportunities.filter(o=>matchesOpportunity(o,{interests,goals,preferences})&&chooseVariant(o,seed.quests,{preferences,stepSize:'Any',defaultEffort:'small'}))}
test('all requested topics, goals, challenge levels and time windows have sample coverage',()=>{
 for(const topic of options.interests)assert.ok(matching([topic]).length,topic);
 for(const goal of options.goals)assert.ok(matching([],[goal]).length,goal);
 for(const challenge of options.challenges)assert.ok(matching([],[],{...base,challenges:[challenge]}).length,challenge);
 for(const time of options.time)assert.ok(matching([],[],{...base,time:[time]}).length,time);
});
test('every topic and goal is required; challenge/time remain alternatives',()=>{
 const preferences={...base,challenges:['Easy','Medium'],time:['5–15 min','15–30 min'],locations:['Online / Remote'],commitment:'Long-term opportunities and projects'};
 const results=matching(['Software Engineering'],['Internship'],preferences);
 assert.ok(results.length);
 for(const o of results){assert.ok(o.topics.includes('Software Engineering'));assert.ok(o.career_goals.includes('Internship'));assert.ok(o.venues.includes('Online / Remote'));assert.equal(o.commitment_type,'long-term');const q=chooseVariant(o,seed.quests,{preferences,stepSize:'Any',defaultEffort:'small'});assert.ok(preferences.challenges.includes(q.difficulty));assert.ok(preferences.time.includes(q.time_bucket));}
});

test('one matching topic cannot satisfy several requested interests',()=>{
 assert.equal(matching(['Software Engineering','Sports']).length,0);
 const record={personalization:{interests:['Productivity & Personal Growth'],filter_interests:[],challenge_levels:['Easy'],time_buckets:['Multi-day'],commitment:base.commitment},career_goals:[],venues:[]};
 assert.equal(matchesOpportunity(record,{interests:['Productivity & Personal Growth'],goals:[],preferences:base}),false);
});
test('empty selections show everything, impossible combinations stay empty, saved records remain independent',()=>{
 assert.equal(matching().length,seed.opportunities.length);
 assert.equal(matching(['Sports'],['Internship']).length,0);
 const hike=seed.opportunities.find(o=>o.topics.includes('Hike'));
 assert.equal(chooseVariant(hike,seed.quests,{stepSize:'Small',preferences:{...base,challenges:['Challenging']},defaultEffort:'small'}),null);
});
