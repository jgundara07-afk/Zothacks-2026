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
