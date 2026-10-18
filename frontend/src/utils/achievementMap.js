export function achievementFraction(badge){
 if(!badge)return 0;
 const target=Number(badge.target);
 if(badge.unlocked)return 1;
 if(!Number.isFinite(target)||target<=0)return 0;
 return Math.min(1,Math.max(0,(Number(badge.progress)||0)/target));
}

export function featuredAchievement(badges=[]){
 const inProgress=badges.filter(badge=>!badge.unlocked&&achievementFraction(badge)>0);
 if(inProgress.length)return [...inProgress].sort((a,b)=>achievementFraction(b)-achievementFraction(a)||a.number-b.number)[0];
 const earned=badges.filter(badge=>badge.unlocked&&badge.earned_at);
 if(earned.length)return [...earned].sort((a,b)=>String(b.earned_at).localeCompare(String(a.earned_at))||b.number-a.number)[0];
 return badges.find(badge=>!badge.unlocked)||badges[0]||null;
}

export function dayInPacific(value){
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(value));
 const part=type=>parts.find(item=>item.type===type)?.value;
 return `${part('year')}-${part('month')}-${part('day')}`;
}

export function trailMomentum(activity=[],today){
 const todayDate=Date.parse(`${today}T00:00:00Z`);
 if(!Number.isFinite(todayDate))return {factor:1,idleDays:0};
 const dayOf=value=>{
  const date=new Date(value);
  if(!Number.isFinite(date.getTime()))return null;
  return dayInPacific(date);
 };
 const days=activity.map(row=>dayOf(row.completed_at)).filter(day=>day&&day<=today);
 if(!days.length)return {factor:1,idleDays:0};
 const lastDate=Date.parse(`${days.sort().at(-1)}T00:00:00Z`);
 const idleDays=Math.max(0,Math.round((todayDate-lastDate)/86400000));
 return {factor:Math.max(0,1-Math.max(0,idleDays-1)*.25),idleDays};
}
