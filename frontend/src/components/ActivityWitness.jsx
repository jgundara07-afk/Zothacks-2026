import React,{useEffect,useRef} from 'react';
import {api} from '../api';
export function publishAchievements(badges){if(badges)window.dispatchEvent(new CustomEvent('onething-achievements',{detail:badges}))}
export default function ActivityWitness({event,recapId,children,onRecorded}){
 const element=useRef(null),recorded=useRef('');
 useEffect(()=>{
  if(!event||!element.current)return;
  const key=event+':'+(recapId||'');if(recorded.current===key)return;
  const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)){
   recorded.current=key;observer.disconnect();
   api.recordEvent({event,...(recapId?{recap_id:recapId}:{})}).then(data=>{publishAchievements(data.achievements);onRecorded?.(data.achievements)}).catch(()=>{recorded.current=''});
  }},{threshold:.1});observer.observe(element.current);return()=>observer.disconnect();
 },[event,recapId]);
 return <div ref={element} style={{minWidth:0}}>{children}</div>;
}
