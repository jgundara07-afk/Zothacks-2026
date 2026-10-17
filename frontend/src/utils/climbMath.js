export function climbPosition(points){
 const safe=Math.max(0,Number(points)||0);
 return {mountain:safe===0?1:Math.ceil(safe/500),fraction:safe===0?0:((safe-1)%500+1)/500,level:Math.floor(safe/100)+1,nextMilestone:(Math.floor(safe/100)+1)*100};
}
export function crossedMilestone(before,after){return after>before&&Math.floor(after/100)>Math.floor(before/100)}
