import React,{useState} from 'react';
import {ArrowRight,ArrowLeft} from 'lucide-react';
import PointsTimeline from '../components/PointsTimeline';

// Wrapped-style recap: every slide is one label, one big number, one plain line. color = a .wrapped.<color> plate.
function buildSlides(data){
 const p=data.progress;
 return [
  {label:'Completed',big:String(p.completed_count),unit:p.completed_count===1?'quest':'quests',color:'purple'},
  {label:'Practice',big:String(data.estimated_minutes),unit:'minutes, estimated',color:'orange'},
  {label:'Top skill',big:data.top_skill||'None yet',unit:data.top_category?`Mostly ${data.top_category}`:'Complete a quest to find yours',color:'lime'},
  {label:'Best streak',big:String(p.longest_streak),unit:p.longest_streak===1?'day':'days',color:'pink'},
 ];
}

export default function Recap({data,onExplore}){
 const [slide,setSlide]=useState(0);
 if(!data)return <p>Loading your recap…</p>;
 const slides=buildSlides(data),item=slides[slide],last=slide===slides.length-1;
 return <><section className={'wrapped '+item.color} aria-label="Progress recap">
  <div className="recap-dots">{slides.map((s,i)=><button key={s.label} aria-label={`Recap slide ${i+1}`} aria-current={i===slide?'step':undefined} onClick={()=>setSlide(i)}/>)}</div>
  <span className="eyebrow">{item.label}</span>
  <div className="recap-big" aria-live="polite" key={slide}>{item.big}<small>{item.unit}</small></div>
  <div className="recap-navigation"><button disabled={slide===0} onClick={()=>setSlide(slide-1)}><ArrowLeft size={18}/> Back</button>{last?<button onClick={onExplore}>Find a quest <ArrowRight size={18}/></button>:<button onClick={()=>setSlide(slide+1)}>Next <ArrowRight size={18}/></button>}</div>
  <details className="recap-method"><summary>How this is counted</summary>From your completed quests. Minutes are estimated from quest durations; skills reflect quest tags, not measured ability.</details>
 </section>
 <PointsTimeline activity={data.progress.activity||[]} today={data.progress.today}/>
 </>
}
