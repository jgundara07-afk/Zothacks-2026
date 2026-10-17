import {test} from 'node:test';
import assert from 'node:assert/strict';
import {activityByDate,monthDays,shiftMonth} from '../src/utils/calendar.js';
test('completion dates follow Pacific midnight and preserve multiple quests per day',()=>{
 const entries=[{completed_at:'2026-10-18T06:59:00Z',quest_id:'one'},{completed_at:'2026-10-18T07:01:00Z',quest_id:'two'},{completed_at:'2026-10-18T18:00:00Z',quest_id:'three'}];
 const days=activityByDate(entries);
 assert.equal(days['2026-10-17'].length,1);
 assert.equal(days['2026-10-18'].length,2);
 assert.equal(Object.keys(days).length,2);
 assert.deepEqual(activityByDate([]),{});
});
test('calendar handles leap years, week padding, and year transitions',()=>{
 const february=monthDays('2024-02').flat();
 assert.equal(february.filter(Boolean).length,29);
 assert.ok(february.includes('2024-02-29'));
 assert.equal(february.length%7,0);
 assert.equal(monthDays('2026-11')[0][0],'2026-11-01');
 assert.equal(shiftMonth('2026-12',1),'2027-01');
 assert.equal(shiftMonth('2026-01',-1),'2025-12');
});
