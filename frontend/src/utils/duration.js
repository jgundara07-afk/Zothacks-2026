export function durationLabel(duration){
 if(!duration)return 'Unknown';
 const {min_minutes:low,max_minutes:high,minutes,quality}=duration;
 const range=high!=null?(low===high?`${high} min`:`${low}–${high} min`):minutes!=null?`${minutes} min`:'Total not provided';
 return `${range} · ${quality|| (duration.estimated?'Estimated':'Source reported')}`;
}
