import {test} from 'node:test';
import assert from 'node:assert/strict';
import {climbPosition,crossedMilestone} from '../src/utils/climbMath.js';
test('climber advances, reaches a summit, and starts a new mountain beyond 500',()=>{
 assert.equal(climbPosition(0).fraction,0);
 assert.equal(climbPosition(100).fraction,.2);
 assert.equal(climbPosition(450).fraction,.9);
 assert.equal(climbPosition(500).fraction,1);
 assert.equal(climbPosition(500).mountain,1);
 assert.equal(climbPosition(550).mountain,2);
 assert.equal(climbPosition(550).fraction,.1);
 assert.equal(climbPosition(1000).fraction,1);
 assert.equal(climbPosition(1000).mountain,2);
});
test('milestones celebrate only newly earned hundreds, including multi-level jumps',()=>{
 assert.equal(crossedMilestone(90,100),true);
 assert.equal(crossedMilestone(99,350),true);
 assert.equal(crossedMilestone(100,115),false);
 assert.equal(crossedMilestone(100,100),false);
 assert.equal(climbPosition(100).nextMilestone,200);
});
