import React,{useEffect,useRef,useState} from 'react';
import Climb from './Climb';
import MountainMap from './MountainMap';
import {dayInPacific,featuredAchievement,trailMomentum} from '../utils/achievementMap';

export default function Atlas({progress,focus=null}){
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
 // A celebration's "See it on the map" focuses its mountain.
 useEffect(()=>{if(focus)setSelectedBadgeId(focus)},[focus]);
 const selected=badges.find(badge=>badge.id===selectedBadgeId)||featuredAchievement(badges);
 const today=progress.today||dayInPacific(Date.now());
 const momentum=trailMomentum(progress.activity||[],today);
 return <section className="journey-atlas" aria-label="Your achievement mountain map">
  {selected?<Climb progress={progress} achievement={selected} momentum={momentum}/>:<p className="journey-atlas-loading" role="status">Your mountains are loading…</p>}
  <MountainMap badges={badges} points={progress.points||0} activeBadgeId={selected?.id} onSelectBadge={setSelectedBadgeId} focus={focus}/>
 </section>;
}
