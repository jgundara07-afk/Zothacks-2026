import React from 'react';

// Points garnered over time: one slim bar per day for the last two weeks. Bar height is the running total,
// and days you earned points are lit. Used on Progress and under the Recap.
export default function PointsTimeline({activity=[],today,days=14}){
 const end=today?new Date(today+'T12:00:00'):new Date();
 const key=d=>d.toLocaleDateString('en-CA');
 const byDay={};
 for(const a of activity){const k=key(new Date(a.completed_at));byDay[k]=(byDay[k]||0)+(a.points||0)}
 const startDate=new Date(end);startDate.setDate(end.getDate()-(days-1));
 let running=activity.filter(a=>new Date(a.completed_at)<new Date(key(startDate)+'T00:00:00')).reduce((t,a)=>t+(a.points||0),0);
 const series=Array.from({length:days},(_,i)=>{const d=new Date(startDate);d.setDate(startDate.getDate()+i);const earned=byDay[key(d)]||0;running+=earned;return {d,earned,total:running}});
 const max=Math.max(1,...series.map(s=>s.total));
 const label=d=>d.toLocaleDateString(undefined,{month:'short',day:'numeric'});
 return <section className="points-timeline" aria-label={`${running} points total over the last ${days} days`}>
  <div className="pt-head"><span className="eyebrow">Points</span><strong>{running}<small> total</small></strong></div>
  <div className="pt-bars" aria-hidden="true">{series.map(s=><span key={key(s.d)} className={s.earned?'earned':''} style={{'--h':`${Math.max(4,s.total/max*100)}%`}} title={`${label(s.d)}: ${s.total} points${s.earned?` (+${s.earned})`:''}`}/>)}</div>
  <div className="pt-axis" aria-hidden="true"><span>{label(series[0].d)}</span><span>Today</span></div>
 </section>
}
