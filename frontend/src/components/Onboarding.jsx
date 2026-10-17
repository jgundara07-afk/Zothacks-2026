import React,{useState,useEffect,useRef} from 'react';
import {ArrowRight,ArrowLeft,Check,Clock3} from 'lucide-react';
import {options} from './PreferenceFields';
import {OPENING_HALFTONE} from '../constants';
import PixelFlame from './PixelFlame';
import {photoFor,scenePhoto,INTEREST_SCENES} from '../utils/photos';

// First-run story, screen by screen (see frontend/ONBOARDING_FLOW.md).
// 0 title card · 1 problem · 2 promise · 3 goals · 4 interests + skills · 5 today · 6 reveal → feed
const SKILLS=['Writing','Coding','Research','Design'];
const NUMERALS=['I','II','III','IV','V','VI','VII','VIII','IX','X'];
// "What can today hold?" sets the step size, which picks each quest's first step (Small / Big) without hiding
// opportunities. The catalog's time windows describe whole opportunities, so they are not used here.
const PACE=[
 {key:'Small',title:'A small step',detail:'A first step you can finish right now.'},
 {key:'Big',title:'Something bigger',detail:'A meatier first step, for when today has room.'},
];
// Only places the catalog can answer without asking for the user's location.
const PLACES=['Online / Remote','On campus'];

function Title({children,className=''}){return <h1 className={'eva '+className}>{children}</h1>}

export default function Onboarding({data,busy,error,hasProfile,interests,setInterests,goals,setGoals,skills,setSkills,preferences,setPreferences,stepSize,setStepSize,sample,topPick,topQuest,onSave,onEnter,onWiden,onSkip}){
 const [step,setStep]=useState(0);
 // Intro plays once per visit; reduced motion goes straight to the finished first screen.
 const [phase,setPhase]=useState(()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches?'ui':'spark');
 useEffect(()=>{
  if(phase==='ui')return;
  const next={spark:['flame',450],flame:['flare',1900],flare:['card',520],card:['ui',2300]}[phase];
  const id=setTimeout(()=>setPhase(next[0]),next[1]);
  return()=>clearTimeout(id);
 },[phase]);
 useEffect(()=>{if(phase==='ui')return;const key=e=>{if(['Enter',' ','Escape'].includes(e.key))setPhase('ui')};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key)},[phase]);
 const skipIntro=()=>setPhase('ui');
 const heading=useRef(null);
 useEffect(()=>{if(step>0||phase==='ui')heading.current?.focus({preventScroll:true})},[step,phase]);
 const next=()=>setStep(s=>Math.min(6,s+1)),back=()=>setStep(s=>Math.max(0,s-1));
 const toggle=(list,set,value,max)=>set(list.includes(value)?list.filter(v=>v!==value):max&&list.length>=max?list:[...list,value]);
 const pace=stepSize;
 const setPace=p=>setStepSize(pace===p.key?'Any':p.key);
 const togglePlace=place=>setPreferences({...preferences,locations:preferences.locations.includes(place)?preferences.locations.filter(v=>v!==place):[...preferences.locations,place]});
 async function finish(){if(await onSave())setStep(6)}

 const chrome=step>0&&step<6&&<header className="ob-bar">
  <button className="ob-back" onClick={back} aria-label="Back"><ArrowLeft size={18}/></button>
  <div className="ob-thread" aria-label={`Step ${step} of 5`}><span style={{width:`${step/5*100}%`}}/></div>
  <button className="ob-skip" disabled={busy||!data} onClick={onSkip}>Skip</button>
 </header>;

 // ---------- 0: intro sequence → title card → first screen ----------
 // spark → flame → flare (light floods the screen) → card (full-screen title) → ui (title rises, panel slides in)
 if(step===0)return <div className={`phone-shell ob ob-title phase-${phase}`} onClick={phase==='ui'?undefined:skipIntro}>
  <div className="ob-title-photo" aria-hidden="true"/>
  <div className="ob-intro" aria-hidden="true">
   <div className="ob-glow"/>
   <PixelFlame className="ob-flame"/>
   <div className="ob-embers">{Array.from({length:10},(_,i)=><i key={i} style={{'--i':i}}/>)}</div>
  </div>
  <div className="ob-flash" aria-hidden="true"/>
  <div className="ob-letterbox ob-letterbox-top" aria-hidden="true"><span>A ZotHacks 2026 Picture</span></div>
  <div className="ob-letterbox ob-letterbox-bottom" aria-hidden="true"><span>One small step at a time</span></div>
  <div className="ob-title-card">
   <span className="ob-ep eva">EPISODE:01</span>
   <h1 className="ob-logo eva">OneThing</h1>
   <p className="ob-tagline eva">A PLACE TO START.</p>
  </div>
  <div className="ob-title-panel" inert={phase==='ui'?undefined:true}>
   <img className="ob-halftone" src={OPENING_HALFTONE} alt="" aria-hidden="true"/>
   <p className="ob-lede" ref={heading} tabIndex={-1}>One small, real step at a time, found for you and worth your while.</p>
   <button className="primary wide" disabled={!data} onClick={next}>{data?'Get started':'Opening the map…'}<ArrowRight size={18}/></button>
   {hasProfile&&<button className="ob-text" disabled={busy} onClick={onSkip}>Continue my journey</button>}
   <small className="ob-fine">ZotHacks demo · fictional profile & sample opportunities · no account needed</small>
  </div>
  {phase!=='ui'&&<button className="ob-skip-intro" onClick={skipIntro}>Skip intro</button>}
 </div>;

 // ---------- 1: problem ----------
 if(step===1)return <div className="phone-shell ob ob-dark">{chrome}
  <div className="ob-problem-photo" aria-hidden="true"/>
  <main className="ob-body ob-problem">
   <Title className="ob-beat"><span ref={heading} tabIndex={-1}>The internet gives you endless possibilities.</span></Title>
   <Title className="ob-beat ob-beat-2">It rarely gives you a <em>starting point.</em></Title>
  </main>
  <footer className="ob-foot"><button className="primary wide" onClick={next}>Show me another way<ArrowRight size={18}/></button></footer>
 </div>;

 // ---------- 2: promise ----------
 if(step===2)return <div className="phone-shell ob ob-map">{chrome}
  <main className="ob-body">
   <span className="ob-chapter">The promise</span>
   <Title><span ref={heading} tabIndex={-1}>One useful thing, small enough to start <em>today.</em></span></Title>
   {sample&&<article className="ob-card">
    <img src={photoFor(sample)} alt=""/>
    <div className="ob-card-text"><span className="ob-card-kicker">{sample.sample!==false&&data?.data_mode!=='catalog'?'Sample':'From the catalog'} · {sample.kind}</span><h2 className="eva">{sample.title}</h2><span className="ob-card-time"><Clock3 size={13}/>{sample.minutes||5} min first step</span></div>
   </article>}
   <p className="ob-note">Every quest has a first step you can finish in one sitting. Small steps count.</p>
  </main>
  <footer className="ob-foot"><button className="primary wide" onClick={next}>Find mine<ArrowRight size={18}/></button></footer>
 </div>;

 // ---------- 3: goals ----------
 if(step===3)return <div className="phone-shell ob ob-map">{chrome}
  <main className="ob-body">
   <span className="ob-chapter">Chapter I · Direction</span>
   <Title><span ref={heading} tabIndex={-1}>What are you moving <em>toward?</em></span></Title>
   <p className="ob-help">Choose up to three. You can change them anytime. <b>{goals.length}/3</b></p>
   <div className="ob-rows" role="group" aria-label="Goals">{options.goals.map((g,i)=><button key={g} className="ob-row" aria-pressed={goals.includes(g)} disabled={!goals.includes(g)&&goals.length>=3} onClick={()=>toggle(goals,setGoals,g,3)}><span className="ob-numeral">{NUMERALS[i]}</span><span>{g}</span>{goals.includes(g)&&<Check size={16}/>}</button>)}</div>
  </main>
  <footer className="ob-foot"><button className="primary wide" onClick={next}>Continue<ArrowRight size={18}/></button></footer>
 </div>;

 // ---------- 4: interests + skills ----------
 if(step===4)return <div className="phone-shell ob ob-map">{chrome}
  <main className="ob-body">
   <span className="ob-chapter">Chapter II · Your kind of things</span>
   <Title><span ref={heading} tabIndex={-1}>What draws you <em>in?</em></span></Title>
   <p className="ob-help">Choose up to three. <b>{interests.length}/3</b></p>
   <div className="ob-tiles" role="group" aria-label="Interests">{options.interests.map(t=><button key={t} className="ob-tile" aria-pressed={interests.includes(t)} disabled={!interests.includes(t)&&interests.length>=3} onClick={()=>toggle(interests,setInterests,t,3)} style={{'--tile':`url(${scenePhoto(INTEREST_SCENES[t]||'train',t)})`}}><span>{t}</span>{interests.includes(t)&&<i className="ob-seal"><Check size={13}/></i>}</button>)}</div>
   <h2 className="ob-sub eva">What could you bring or <em>practice?</em></h2>
   <div className="choice-tags" role="group" aria-label="Skills">{SKILLS.map(s=><button key={s} type="button" aria-pressed={skills.includes(s)} onClick={()=>toggle(skills,setSkills,s)}>{skills.includes(s)&&<Check size={13}/>} {s}</button>)}</div>
  </main>
  <footer className="ob-foot"><button className="primary wide" disabled={!interests.length||!skills.length} onClick={next}>Continue<ArrowRight size={18}/></button>{(!interests.length||!skills.length)&&<small className="ob-fine">Pick at least one interest and one skill.</small>}</footer>
 </div>;

 // ---------- 5: today ----------
 if(step===5)return <div className="phone-shell ob ob-map">{chrome}
  <main className="ob-body">
   <span className="ob-chapter">Chapter III · Today</span>
   <Title><span ref={heading} tabIndex={-1}>What can today <em>hold?</em></span></Title>
   <div className="ob-pace" role="radiogroup" aria-label="Step size">{PACE.map(p=><button key={p.key} role="radio" aria-checked={pace===p.key} className="ob-pace-card" onClick={()=>setPace(p)}><strong className="eva">{p.title}</strong><span>{p.detail}</span></button>)}</div>
   <h2 className="ob-sub eva">Where should we <em>look?</em></h2>
   <div className="choice-tags" role="group" aria-label="Where">{PLACES.map(p=><button key={p} type="button" aria-pressed={preferences.locations.includes(p)} onClick={()=>togglePlace(p)}>{preferences.locations.includes(p)&&<Check size={13}/>} {p}</button>)}</div>
   <p className="ob-note">Leave it open to see everything. A small step counts just as much.</p>
   {error&&<p className="error" role="alert">{error}</p>}
  </main>
  <footer className="ob-foot"><button className="primary wide" disabled={busy} onClick={finish}>{busy?'Charting your map…':'Show my one thing'}<ArrowRight size={18}/></button></footer>
 </div>;

 // ---------- 6: reveal ----------
 return <div className="phone-shell ob ob-reveal">
  {topPick&&<div className="ob-reveal-photo" style={{'--photo':`url(${photoFor(topPick)})`}} aria-hidden="true"/>}
  <main className="ob-body ob-reveal-body">
   <span className="ob-chapter">Your first quest</span>
   <Title><span ref={heading} tabIndex={-1}>Start <em>here.</em></span></Title>
   {topPick?<article className="ob-reveal-card">
    <span className="ob-card-kicker">{data?.data_mode==='catalog'?'From the catalog':'Sample'} · {topPick.kind}{topPick.mode?` · ${topPick.mode}`:''}</span>
    <h2 className="eva">{topPick.title}</h2>
    <p className="ob-why">{topPick.matching_tags?.length?`Because you chose ${topPick.matching_tags.slice(0,2).join(' and ')}.`:'A new direction worth a look.'}</p>
    {topQuest&&<div className="ob-first-step"><span>First step · {topQuest.minutes||topPick.minutes} min</span><strong>{topQuest.title}</strong></div>}
   </article>:<div className="ob-empty"><p className="ob-why">Your exact mix is rare. Nothing in the catalog matches every choice at once.</p><p className="ob-note">Widen the search to start from your first interest, or change your answers.</p></div>}
  </main>
  <footer className="ob-foot">{topPick?<button className="primary wide" onClick={onEnter}>Explore the feed<ArrowRight size={18}/></button>:<><button className="primary wide" disabled={busy} onClick={onWiden}>Widen my search<ArrowRight size={18}/></button><button className="ob-text" onClick={()=>setStep(3)}>Change my answers</button></>}</footer>
 </div>;
}
