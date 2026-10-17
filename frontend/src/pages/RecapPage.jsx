import React,{useEffect,useState} from 'react';
import {ArrowRight,ArrowLeft,Pause,Play,RotateCcw} from 'lucide-react';
import PointsTimeline from '../components/PointsTimeline';
import {api} from '../api';

const DURATION=4600;

function slidesFor(data,story){
 const p=data.progress||{};
 const latest=[...(p.activity||[])].sort((a,b)=>b.completed_at.localeCompare(a.completed_at))[0];
 const completed=p.completed_count||0;
 const chapter=Math.floor((p.points||0)/100)+1;
 return [
  {label:'Your story so far',big:String(p.points||0),unit:'points earned',body:`From ${completed} completed ${completed===1?'step':'steps'}. Every mark on your map came from something you actually did.`,color:'purple'},
  {label:'Time you gave yourself',big:String(data.estimated_minutes||0),unit:'minutes estimated',body:latest?`Most recently: “${latest.title}.” Your time estimate is based on the quests you marked complete.`:'Complete a quest to start your story.',color:'orange'},
  {label:'What you practiced',big:data.top_skill||'A first skill',unit:data.top_category?`Most steps: ${data.top_category}`:'Your skills emerge as you complete steps',body:data.top_skill?`${data.top_skill} appears most often in your completed quest tags. This shows practice, not measured proficiency.`:'Your first quest will give this chapter a focus.',color:'pink'},
  {label:'The route keeps growing',big:`CHAPTER ${chapter}`,unit:`${p.points||0} lifetime points`,body:`${p.longest_streak||0} ${p.longest_streak===1?'day':'days'} at your best streak. Your next region opens at ${chapter*100} points.`,color:'lime'},
  {label:'Your next chapter',big:story?.archetype||'Keep going',unit:story?.evidence||`${completed} completed steps`,body:story?.next_step||'Choose one manageable next step.',color:'purple'},
 ];
}

export default function Recap({data,onExplore}){
 const [slide,setSlide]=useState(0);
 const [playing,setPlaying]=useState(()=>!window.matchMedia('(prefers-reduced-motion: reduce)').matches);
 const [story,setStory]=useState(null);
 useEffect(()=>{let active=true;api.recapNarrative().then(result=>{if(active&&result?.narrative)setStory(result)}).catch(()=>{});return()=>{active=false}},[]);
 const complete=data?.progress?.completed_count||0;
 const slides=data?slidesFor(data,story?.narrative):[];
 useEffect(()=>{if(!playing||!complete||slide>=slides.length-1)return;const timer=setTimeout(()=>setSlide(s=>s+1),DURATION);return()=>clearTimeout(timer)},[playing,complete,slide,slides.length]);
 if(!data)return <p role="status">Loading your recap…</p>;
 if(!complete)return <section className="wrapped purple recap-empty"><span className="eyebrow">YOUR STORY STARTS HERE</span><h2>No completed quests yet.</h2><p>Save a promising opportunity and finish one preparation step. Your recap will grow from what you actually do.</p><button className="primary" onClick={onExplore}>Find my first quest <ArrowRight size={18}/></button></section>;
 const item=slides[slide],last=slide===slides.length-1;
 function go(index){setPlaying(false);setSlide(index)}
 return <><section className={`wrapped ${item.color} recap-stage`} aria-label="Progress recap" aria-roledescription="slideshow">
  <div className="recap-dots">{slides.map((s,i)=><button key={s.label} aria-label={`Recap slide ${i+1}: ${s.label}`} aria-current={i===slide?'step':undefined} onClick={()=>go(i)}><span className={playing&&i===slide?'recap-dot-playing':''} style={{'--recap-duration':`${DURATION}ms`}}/></button>)}</div>
  <div className="recap-stage-head"><span className="eyebrow">{String(slide+1).padStart(2,'0')} / {String(slides.length).padStart(2,'0')} · {item.label}</span><button className="recap-play" aria-label={playing?'Pause recap':'Play recap'} onClick={()=>setPlaying(v=>!v)}>{playing?<Pause size={16}/>:<Play size={16}/>}</button></div>
  <div className="recap-scene" key={slide}><div className="recap-big">{item.big}<small>{item.unit}</small></div><p className="recap-story">{item.body}</p></div>
  {last&&story?.source==='gemini'&&<span className="recap-ai-label">Narrative by Gemini · counts from your completed quests</span>}
  <div className="recap-navigation"><button disabled={slide===0} onClick={()=>go(slide-1)}><ArrowLeft size={18}/> Back</button>{last?<><button onClick={()=>{setSlide(0);setPlaying(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)}}><RotateCcw size={16}/> Replay</button><button onClick={onExplore}>Find a quest <ArrowRight size={18}/></button></>:<button onClick={()=>go(slide+1)}>Next <ArrowRight size={18}/></button>}</div>
  <details className="recap-method"><summary>How this is counted</summary>Counts and skills come from recorded quest completions. Quest time is estimated. Chapter numbers use lifetime points. The archetype is a playful description, not an assessment of ability.</details>
 </section><PointsTimeline activity={data.progress.activity||[]} today={data.progress.today}/></>;
}
