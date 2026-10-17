// On Discover with a difficulty picked, swap each card's default quest for its daily quest at that difficulty.
export function withDifficultyVariants(opportunities,quests,page,difficulty){
 return opportunities.map(o=>{
  const variant=page!=='Discover'||difficulty==='Any'?null:quests.find(q=>q.opportunity_id===o.id&&q.difficulty===difficulty&&q.daily);
  return variant?{...o,minutes:variant.minutes,suggested_quest_id:variant.id,effort:variant.effort,difficulty:variant.difficulty}:o;
 });
}

// Saved things only shows saved cards; the detailed filters only apply on Discover.
export function filterOpportunities(opportunities,page,filters){
 const {topic,source,mode,goal,skill,gapSkills}=filters;
 return opportunities.filter(o=>(page!=='Saved things'||o.saved)&&(topic==='All opportunities'||o.tags.includes(topic))&&(page!=='Discover'||((source==='All sources'||o.kind===source)&&(mode==='Anywhere'||o.mode===mode)&&(goal==='Any goal'||o.goals?.includes(goal))&&(skill==='Any skill'||o.skills?.includes(skill))&&(!gapSkills.length||o.skills?.some(t=>gapSkills.includes(t))))));
}

export const toggleItem=(list,value)=>list.includes(value)?list.filter(x=>x!==value):[...list,value];
