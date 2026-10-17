import React,{useState} from 'react';
import {Check,Flag} from 'lucide-react';
import Climb from './Climb';

function dayInPacific(value){
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(value));
 const part=type=>parts.find(item=>item.type===type)?.value;
 return `${part('year')}-${part('month')}-${part('day')}`;
}

function periodActivity(activity,today,period){
 if(period==='all')return activity;
 const start=new Date(`${today}T12:00:00Z`);
 if(period==='week')start.setUTCDate(start.getUTCDate()-(start.getUTCDay()+6)%7);
 else start.setUTCDate(1);
 const first=start.toISOString().slice(0,10);
 return activity.filter(item=>{const day=dayInPacific(item.completed_at);return day>=first&&day<=today});
}

export default function Atlas({progress,fromPoints}){
 const [period,setPeriod]=useState('week');
 const today=progress.today||dayInPacific(Date.now());
 const activity=periodActivity(progress.activity||[],today,period);
 const points=activity.reduce((sum,item)=>sum+(Number(item.points)||0),0);
 const currentChapter=Math.floor((progress.points||0)/100)+1;
 const chapters=Array.from({length:Math.min(currentChapter+1,12)},(_,index)=>index+1);
 return <section className="atlas" aria-label="Your growing map">
  <Climb progress={progress} fromPoints={fromPoints}/>
  <div className="atlas-ledger">
   <div className="atlas-heading"><span className="atlas-kicker">THE ROUTE SO FAR</span><p>Each completed quest extends the path. A new region opens every 100 points.</p></div>
   <div className="atlas-periods" role="group" aria-label="Map activity period">{[['week','This week'],['month','This month'],['all','All time']].map(([value,label])=><button key={value} aria-pressed={period===value} onClick={()=>setPeriod(value)}>{label}</button>)}</div>
   <p className="atlas-period-stat" aria-live="polite"><strong>{points}</strong> points earned through <strong>{activity.length}</strong> completed {activity.length===1?'step':'steps'} {period==='all'?'overall':period==='week'?'this week':'this month'}.</p>
   <ol className="atlas-chapters">{chapters.map(chapter=><li key={chapter} className={chapter<currentChapter?'explored':chapter===currentChapter?'current':'unseen'}><span className="atlas-node" aria-hidden="true">{chapter<currentChapter?<Check size={14}/>:chapter===currentChapter?<Flag size={14}/>:chapter}</span><div><strong>{chapter<currentChapter?`Chapter ${chapter} · explored`:chapter===currentChapter?`Chapter ${chapter} · underway`:'Uncharted territory'}</strong><small>{(chapter-1)*100}–{chapter*100} points</small></div></li>)}</ol>
   <small className="atlas-footnote">The period changes the activity count; the route always shows your lifetime progress.</small>
  </div>
 </section>;
}
