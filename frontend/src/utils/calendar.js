export function activityByDate(activity, timeZone='America/Los_Angeles') {
 const grouped={};
 const formatter=new Intl.DateTimeFormat('en-US',{timeZone,year:'numeric',month:'2-digit',day:'2-digit'});
 for(const entry of activity){
  const date=new Date(entry.completed_at);
  if(Number.isNaN(date.getTime()))continue;
  const parts=Object.fromEntries(formatter.formatToParts(date).map(p=>[p.type,p.value]));
  const key=`${parts.year}-${parts.month}-${parts.day}`;
  (grouped[key]||=[]).push(entry);
 }
 return grouped;
}
export function monthDays(month) {
 const [year,number]=month.split('-').map(Number);
 const offset=new Date(Date.UTC(year,number-1,1)).getUTCDay();
 const total=new Date(Date.UTC(year,number,0)).getUTCDate();
 const cells=Array(offset).fill(null);
 for(let day=1;day<=total;day++)cells.push(`${month}-${String(day).padStart(2,'0')}`);
 while(cells.length%7)cells.push(null);
 return Array.from({length:cells.length/7},(_,i)=>cells.slice(i*7,i*7+7));
}
export function shiftMonth(month,direction){
 const [year,number]=month.split('-').map(Number);
 return new Date(Date.UTC(year,number-1+direction,1)).toISOString().slice(0,7);
}
