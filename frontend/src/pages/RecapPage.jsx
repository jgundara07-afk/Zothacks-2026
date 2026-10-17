import React,{useEffect,useState} from 'react';
import {ArrowRight,ArrowLeft} from 'lucide-react';
import PointsTimeline from '../components/PointsTimeline';
import {api} from '../api';

function localStory(data){
 const category=data.categories?Object.entries(data.categories).sort((a,b)=>b[1]-a[1])[0]:null;
 const skill=data.top_skill;
 const labels={'General task':'The Small-Step Strategist','Online course':'The Skill Collector','Certification':'The Skill Collector',Class:'The Curious Scholar',Internship:'The Career Pathfinder','Job simulation':'The Career Pathfinder',Networking:'The Connector',Club:'The Community Builder',Park:'The Trailblazer'};
 const done=data.completed_count||0;
 if(!done)return {source:'local',narrative:{archetype:'The First-Step Scout',evidence:'Your recap is ready for your first completed quest.',description:'Your OneThing story is just getting started. One small step will give the next recap its first chapter.',quest_line:'The opening track is still yours to choose.',onething_line:'No points yet, and all the possibility in front of you.',next_step:'Pick one short quest and take its first step.'}};
 const [kind,count]=category||['quest',done];
 return {source:'local',narrative:{archetype:labels[kind]||'The OneThing Climber',evidence:`${count} completed ${kind} quests${skill?` · most practiced skill: ${skill}`:''}`,description:`Your completed work leaned toward ${kind}. You kept turning a little time into visible progress, one quest at a time.`,quest_line:'Your completed quests made quite a highlight reel. OneThing saw you show up.',onething_line:`${done} completed steps and ${data.points||0} points: proof that small things add up.`,next_step:skill?`Choose one manageable quest that builds on ${skill}.`:'Choose one manageable quest to start your next chapter.'}};
}

function buildSlides(data,story){
 const p=data.progress||{};
 const n=story.narrative;
 return [
  {label:'Completed',big:String(p.completed_count||0),unit:(p.completed_count||0)===1?'quest':'quests',color:'purple'},
  {label:'Practice',big:String(data.estimated_minutes||0),unit:'minutes, estimated',color:'orange'},
  {label:'Your archetype',big:n.archetype,unit:n.evidence,body:n.description,color:'lime',ai:true},
  {label:'Quest highlights',big:'You did the thing.',unit:'and made it count.',body:n.quest_line,color:'pink',ai:true},
  {label:'Top skill',big:data.top_skill||'None yet',unit:data.top_category?`Mostly ${data.top_category}`:'Complete a quest to find yours',color:'purple'},
  {label:'OneThing energy',big:'Small steps.',unit:'big plot.',body:n.onething_line,color:'orange',ai:true},
  {label:'Next chapter',big:'Your next move',unit:'One thing at a time',body:n.next_step,color:'lime',ai:true},
  {label:'Best streak',big:String(p.longest_streak||0),unit:(p.longest_streak||0)===1?'day':'days',color:'pink'},
 ];
}

export default function Recap({data,onExplore}){
 const [slide,setSlide]=useState(0);
 const [story,setStory]=useState(()=>localStory(data||{}));
 useEffect(()=>{let active=true;api.recapNarrative().then(result=>{if(active&&result?.narrative)setStory(result)}).catch(()=>{});return()=>{active=false}},[]);
 if(!data)return <p>Loading your recap…</p>;
 const slides=buildSlides(data,story),item=slides[slide],last=slide===slides.length-1;
 return <><section className={'wrapped '+item.color} aria-label="Progress recap">
  <div className="recap-dots">{slides.map((s,i)=><button key={s.label} aria-label={`Recap slide ${i+1}: ${s.label}`} aria-current={i===slide?'step':undefined} onClick={()=>setSlide(i)}/>)}</div>
  <span className="eyebrow">{item.label}</span>
  <div className="recap-big" aria-live="polite" key={slide}>{item.big}<small>{item.unit}</small></div>
  {item.body&&<p className="recap-story">{item.body}</p>}
  {item.ai&&story.source==='gemini'&&<span className="recap-ai-label">Gemini story · based on your completed quests</span>}
  <div className="recap-navigation"><button disabled={slide===0} onClick={()=>setSlide(slide-1)}><ArrowLeft size={18}/> Back</button>{last?<button onClick={onExplore}>Find a quest <ArrowRight size={18}/></button>:<button onClick={()=>setSlide(slide+1)}>Next <ArrowRight size={18}/></button>}</div>
  <details className="recap-method"><summary>How this is counted</summary>Counts and skills come from recorded quest completions. Quest time is estimated. The archetype and story are playful descriptions of this activity, not assessments of ability. {story.source==='gemini'?'Gemini wrote the recap from your category, skill, difficulty, and recent completed-quest records.':'A local recap is shown because Gemini was unavailable.'}</details>
 </section>
 <PointsTimeline activity={data.progress.activity||[]} today={data.progress.today}/>
 </>
}
