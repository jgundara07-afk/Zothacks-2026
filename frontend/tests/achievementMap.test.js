import test from 'node:test';
import assert from 'node:assert/strict';
import {achievementFraction,featuredAchievement} from '../src/utils/achievementMap.js';

test('a mountain marker follows achievement progress and stops at the summit',()=>{
 assert.equal(achievementFraction({progress:3,target:4,unlocked:false}),.75);
 assert.equal(achievementFraction({progress:0,target:4,unlocked:true}),1);
 assert.equal(achievementFraction({progress:9,target:4,unlocked:false}),1);
 assert.equal(achievementFraction({progress:0,target:0,unlocked:false}),0);
});

test('the featured route prioritizes an unfinished mountain with progress',()=>{
 const badges=[
  {id:'earned',number:1,progress:1,target:1,unlocked:true,earned_at:'2026-10-01'},
  {id:'started',number:2,progress:3,target:4,unlocked:false},
  {id:'untouched',number:3,progress:0,target:10,unlocked:false},
 ];
 assert.equal(featuredAchievement(badges).id,'started');
 assert.equal(featuredAchievement([badges[0],badges[2]]).id,'earned');
 assert.equal(featuredAchievement([]),null);
});
