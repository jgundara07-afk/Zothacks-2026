import {test} from 'node:test';
import assert from 'node:assert/strict';
import {climbPosition,crossedMilestone} from '../src/utils/climbMath.js';
test('map and countdown use the same hundred-point milestone',()=>{
 for(const points of [0,25,75,99,100,175,450,500,550,1000]){
  const position=climbPosition(points);
  assert.equal(position.fraction,(points%100)/100);
  assert.equal(position.mountain,Math.floor(points/100)+1);
  assert.equal(position.nextMilestone-points,100-position.fraction*100);
 }
 assert.equal(climbPosition(175).fraction,.75);
 assert.equal(climbPosition(175).nextMilestone-175,25);
});
test('milestones celebrate only newly earned hundreds, including multi-level jumps',()=>{
 assert.equal(crossedMilestone(90,100),true);
 assert.equal(crossedMilestone(99,350),true);
 assert.equal(crossedMilestone(100,115),false);
 assert.equal(crossedMilestone(100,100),false);
 assert.equal(climbPosition(100).nextMilestone,200);
});
