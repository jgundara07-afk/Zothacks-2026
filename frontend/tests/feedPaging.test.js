import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mergeFeedPage,nextFeedOffset} from '../src/utils/feedPaging.js';
test('append preserves previous cards and saves, deduplicates overlapping IDs, advances using server offset',()=>{
 const old={offset:0,page_count:2,opportunities:[{id:'a',saved:true},{id:'b',saved:false}],has_more:true};
 const page={offset:2,page_count:2,opportunities:[{id:'b',saved:true},{id:'c',saved:false}],has_more:true,total:10};
 const merged=mergeFeedPage(old,page);
 assert.deepEqual(merged.opportunities.map(o=>o.id),['a','b','c']);
 assert.equal(merged.opportunities[0].saved,true);
 assert.equal(merged.opportunities[1].saved,true);
 assert.equal(nextFeedOffset(merged),4);
});
test('new filters replace the feed; final page and empty result stop pagination',()=>{
 const result=mergeFeedPage(null,{offset:0,page_count:1,opportunities:[{id:'new-filter'}],has_more:false});
 assert.deepEqual(result.opportunities.map(o=>o.id),['new-filter']);
 assert.equal(result.has_more,false);
 assert.equal(nextFeedOffset(null),0);
 assert.equal(mergeFeedPage(null,{opportunities:[],has_more:false}).opportunities.length,0);
});
