import React,{useEffect,useState} from 'react';
import {SlidersHorizontal,ChevronDown,X} from 'lucide-react';

// The only filter control: a slim bar at the top of the feed. It slides out of view while you scroll down
// (like a TikTok/Instagram header) and back when you scroll up. Its chip list is a dropdown you can close,
// and the × tucks the whole bar away until the next upward scroll.
export default function FilterBar({feedRef,count,chips,notes=[],onOpen}){
 const [shown,setShown]=useState(true),[expanded,setExpanded]=useState(false);
 useEffect(()=>{
  const el=feedRef.current;if(!el)return;
  let last=el.scrollTop;
  const onScroll=()=>{const y=el.scrollTop;if(Math.abs(y-last)<12)return;setShown(y<last||y<40);if(y>last)setExpanded(false);last=y};
  el.addEventListener('scroll',onScroll,{passive:true});
  return()=>el.removeEventListener('scroll',onScroll);
 },[feedRef.current]);
 return <div className={`filter-bar ${shown?'':'is-hidden'}`} role="region" aria-label="Feed filters">
  <div className="filter-bar-row">
   <button className="filter-bar-open" onClick={onOpen}><SlidersHorizontal size={16}/>Filters{count>0&&<b>{count}</b>}</button>
   {chips.length>0&&<button className="filter-bar-summary" aria-expanded={expanded} onClick={()=>setExpanded(e=>!e)}>Your filters<ChevronDown size={15}/></button>}
   <button className="filter-bar-close" aria-label="Hide filters" onClick={()=>{setExpanded(false);setShown(false)}}><X size={16}/></button>
  </div>
  {expanded&&<div className="filter-bar-drop">
   {notes.map(note=><small key={note}>{note}</small>)}
   <div className="filter-bar-chips">{chips.map((chip,i)=><button key={chip.label+i} onClick={chip.remove} aria-label={`Remove filter: ${chip.label}`}>{chip.label}<X size={12}/></button>)}</div>
  </div>}
 </div>
}
