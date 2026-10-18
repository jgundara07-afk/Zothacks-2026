import React,{useEffect,useRef} from 'react';
import {Flag,ArrowRight} from 'lucide-react';
import {BadgeMedallion} from './AchievementGallery';
import {REGIONS,mountainName} from '../utils/achievementRegions';

// Shown once per newly unlocked achievement (App queues them). The medal is struck in gold over the map;
// reduced motion shows the same card without the spin, rays or dust.
export default function AchievementUnlock({badge,remaining=0,onClose,onView}){
 const card=useRef(null),close=useRef(onClose);close.current=onClose;
 useEffect(()=>{
  const previous=document.activeElement,buttons=()=>Array.from(card.current?.querySelectorAll('button')||[]);
  buttons()[0]?.focus();
  const keydown=e=>{
   if(e.key==='Escape'){e.preventDefault();close.current()}
   if(e.key==='Tab'){const items=buttons(),first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}
  };
  document.addEventListener('keydown',keydown);
  return()=>{document.removeEventListener('keydown',keydown);previous?.focus?.()};
 },[badge.id]);
 const region=REGIONS.find(([id])=>id===(badge.region||'foundations'))?.[1],peak=mountainName(badge);
 return <div className="unlock-overlay" role="dialog" aria-modal="true" aria-labelledby="unlock-title" aria-describedby="unlock-criteria" key={badge.id}>
  <div className="unlock-rays" aria-hidden="true"/>
  <div className="unlock-dust" aria-hidden="true">{Array.from({length:16},(_,i)=><i key={i} style={{'--i':i}}/>)}</div>
  <section className="unlock-card" ref={card}>
   <span className="unlock-eyebrow">Achievement unlocked</span>
   <div className="unlock-medal"><span className="unlock-flash" aria-hidden="true"/><BadgeMedallion badge={{...badge,unlocked:true}}/></div>
   <h2 id="unlock-title" className="unlock-name">{badge.name}</h2>
   <p className="unlock-peak"><Flag size={14}/>{[peak!==badge.name&&peak,region].filter(Boolean).join(' · ')}</p>
   <p id="unlock-criteria" className="unlock-criteria">{badge.criteria}</p>
   {badge.flavor&&<blockquote className="unlock-flavor">“{badge.flavor}”</blockquote>}
   <p className="unlock-note">A new peak is charted on your map.</p>
   <div className="unlock-actions"><button className="primary wide" onClick={onClose}>{remaining?`Next achievement · ${remaining} more`:'Continue'}<ArrowRight size={17}/></button><button className="text-link" onClick={onView}>See it on the map</button></div>
  </section>
 </div>;
}
