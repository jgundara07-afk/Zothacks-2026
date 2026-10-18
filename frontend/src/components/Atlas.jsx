import React,{useEffect,useRef,useState} from 'react';
import Climb from './Climb';
import MountainMap from './MountainMap';
import {featuredAchievement} from '../utils/achievementMap';

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

export default function Atlas({progress}){
 const [period,setPeriod]=useState('week');
 const [selectedBadgeId,setSelectedBadgeId]=useState(null);
 const previousUnlocks=useRef(null);
 const badges=progress.achievements||[];
 useEffect(()=>{
  if(!badges.length)return;
  const unlocked=new Set(badges.filter(badge=>badge.unlocked).map(badge=>badge.id));
  if(previousUnlocks.current){
   const newlyEarned=badges.find(badge=>unlocked.has(badge.id)&&!previousUnlocks.current.has(badge.id));
   if(newlyEarned)setSelectedBadgeId(newlyEarned.id);
  }
  previousUnlocks.current=unlocked;
 },[badges]);
 const selected=badges.find(badge=>badge.id===selectedBadgeId)||featuredAchievement(badges);
 const today=progress.today||dayInPacific(Date.now());
 const activity=periodActivity(progress.activity||[],today,period);
 const points=activity.reduce((sum,item)=>sum+(Number(item.points)||0),0);
 return <section className="journey-atlas" aria-label="Your achievement mountain map">
  {selected?<Climb progress={progress} achievement={selected}/>:<p className="journey-atlas-loading" role="status">Your mountains are loading…</p>}
  <div className="journey-atlas-ledger">
   <div className="journey-atlas-heading"><span className="journey-atlas-kicker">YOUR ACHIEVEMENT ROUTE</span><p>Each achievement is a mountain. The checkmark climbs as you complete its goal. Choose a mountain below to see your route.</p></div>
   <div className="journey-atlas-periods" role="group" aria-label="Map activity period">{[['week','This week'],['month','This month'],['all','All time']].map(([value,label])=><button key={value} aria-pressed={period===value} onClick={()=>setPeriod(value)}>{label}</button>)}</div>
   <p className="journey-atlas-period-stat" aria-live="polite"><strong>{points}</strong> points earned through <strong>{activity.length}</strong> completed {activity.length===1?'step':'steps'} {period==='all'?'overall':period==='week'?'this week':'this month'}.</p>
   <small className="journey-atlas-footnote">The period changes the activity count; mountain progress and earned achievements are lifetime totals.</small>
  </div>
  <MountainMap badges={badges} points={progress.points||0} activeBadgeId={selected?.id} onSelectBadge={setSelectedBadgeId}/>
 </section>;
}
