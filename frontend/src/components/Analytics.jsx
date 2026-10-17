import React from 'react';
import {ArrowRight,Sparkles} from 'lucide-react';

// Stats, seven-day bar chart and skill/category breakdown on My progress.
export default function Analytics({data,onRecap}){
 if(!data)return <p>Loading your little wins…</p>;
 const p=data.progress,max=Math.max(1,...data.week.map(d=>d.count));
 return <section className="analytics-panel"><div className="section-heading"><h2>Your progress, in perspective</h2><Sparkles size={19}/></div><p>Every useful step leaves a little trail.</p>
  <div className="analytics-stats"><div><strong>{data.active_days}</strong><span>active days</span></div><div><strong>{data.estimated_minutes}</strong><span>estimated minutes</span></div><div><strong>{p.streak}</strong><span>day streak</span></div></div>
  <h3>Your last seven days</h3>
  <div className="week-chart" role="img" aria-label={data.week.map(d=>`${d.date}: ${d.count} quests`).join('; ')}>{data.week.map(d=><div key={d.date}><span className="bar-value">{d.count}</span><div className="bar-track"><span style={{height:`${d.count/max*100}%`}}/></div><small>{new Date(d.date+'T12:00:00').toLocaleDateString(undefined,{weekday:'short'})}</small></div>)}</div>
  <div className="breakdown-grid">{[['Skills practiced',data.skills],['Your opportunity mix',data.categories]].map(([title,values])=><div key={title}><h3>{title}</h3>{Object.entries(values).length?Object.entries(values).map(([name,count])=><div className="breakdown" key={name}><span>{name}</span><b>{count}</b></div>):<p>Complete a quest to see your mix.</p>}</div>)}</div>
  <p className="method-note">{data.method} Skill counts reflect quest tags, not measured proficiency.</p>
  <button className="primary" onClick={onRecap}>Play my progress recap <ArrowRight size={16}/></button>
 </section>
}
