export function chooseVariant(o,quests,{stepSize,preferences,defaultEffort}){
 const candidates=quests.filter(q=>q.opportunity_id===o.id&&q.daily&&(!preferences.challenges.length||preferences.challenges.includes(q.difficulty))&&(stepSize==='Any'||q.size===stepSize)&&(!preferences.time.length||preferences.time.some(t=>t==='Multi-day'?o.multi_day:q.time_bucket===t)));
 const sorted=[...candidates].sort((a,b)=>(a.effort===defaultEffort?0:1)-(b.effort===defaultEffort?0:1)||a.minutes-b.minutes);
 return sorted[0]||null;
}
export function matchesOpportunity(o,{interests,goals,preferences}){
 return (!interests.length||interests.some(t=>o.topics?.includes(t)))&&(!goals.length||goals.some(g=>o.career_goals?.includes(g)))&&(!preferences.locations.length||preferences.locations.some(l=>o.venues?.includes(l)))&&(preferences.commitment==='A mix of both'||preferences.commitment==='Quick tasks I can finish immediately'&&o.commitment_type==='quick'||preferences.commitment==='Long-term opportunities and projects'&&o.commitment_type==='long-term');
}
