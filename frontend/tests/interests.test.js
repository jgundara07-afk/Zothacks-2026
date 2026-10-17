import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {searchInterests,interestCatalog} from '../src/utils/interests.js';

test('all categorized interests exist in both UI and backend taxonomy without case duplicates',()=>{
 const preferences=JSON.parse(readFileSync(new URL('../../shared/preferences.json',import.meta.url)));
 const taxonomy=JSON.parse(readFileSync(new URL('../../opportunity_data/taxonomy.json',import.meta.url)));
 const all=searchInterests(interestCatalog.groups);
 assert.equal(all.length,462);
 assert.deepEqual(all,preferences.interests);
 assert.deepEqual(taxonomy.interests,preferences.interests);
 assert.equal(new Set(all.map(s=>s.toLowerCase())).size,all.length);
 assert.equal(taxonomy.max_selected_interests,10);
});
test('search and category narrowing include new choices',()=>{
 assert.ok(searchInterests(interestCatalog.groups,'robot').includes('Robotics'));
 assert.ok(searchInterests(interestCatalog.groups,'front develop').includes('Frontend development'));
 assert.ok(searchInterests(interestCatalog.groups,'','Lifestyle, Travel & Culture').includes('Cooking'));
 assert.ok(!searchInterests(interestCatalog.groups,'','Lifestyle, Travel & Culture').includes('Robotics'));
});
