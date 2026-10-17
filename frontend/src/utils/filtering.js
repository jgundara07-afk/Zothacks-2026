export function chooseVariant(o,quests,{stepSize,preferences,defaultEffort}){
 const collected=!!o.personalization&&!o.sample;
 const candidates=quests.filter(q=>q.opportunity_id===o.id&&q.daily&&(collected||!preferences.challenges.length||preferences.challenges.includes(q.difficulty))&&(stepSize==='Any'||q.size===stepSize)&&(collected||!preferences.time.length||preferences.time.some(t=>t==='Multi-day'?o.multi_day:q.time_bucket===t)));
 const sorted=[...candidates].sort((a,b)=>(a.effort===defaultEffort?0:1)-(b.effort===defaultEffort?0:1)||a.minutes-b.minutes);
 return sorted[0]||null;
}
export function matchesOpportunity(o,{interests,goals,preferences}){
 const p=o.personalization&&!o.sample?o.personalization:null;
 return (!interests.length||interests.every(t=>(p?.filter_interests||p?.interests||o.topics)?.includes(t)))&&(!goals.length||goals.every(g=>o.career_goals?.includes(g)))&&(!preferences.locations.length||preferences.locations.some(l=>o.venues?.includes(l)))&&(!p||(!preferences.challenges.length||preferences.challenges.some(v=>p.challenge_levels.includes(v)))&&(!preferences.time.length||preferences.time.some(v=>p.time_buckets.includes(v))))&&(preferences.commitment==='A mix of both'||(p?preferences.commitment===p.commitment:preferences.commitment==='Quick tasks I can finish immediately'&&o.commitment_type==='quick'||preferences.commitment==='Long-term opportunities and projects'&&o.commitment_type==='long-term'));
}
