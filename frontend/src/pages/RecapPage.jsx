import React,{useEffect,useState} from 'react';
import {ArrowRight,ArrowLeft,Sparkles,Award} from 'lucide-react';
import AchievementGallery from '../components/AchievementGallery';
import ActivityWitness,{publishAchievements} from '../components/ActivityWitness';
import RecapHighlights from '../components/RecapHighlights';
import {api} from '../api';

function localStory(data){
 const category=data?.top_category,skill=data?.top_skill,done=data?.completed_count||0;
 const labels={'General task':'The Small-Step Strategist','Online course':'The Skill Collector',Certification:'The Skill Collector',Class:'The Curious Scholar',Internship:'The Career Pathfinder',Networking:'The Connector',Club:'The Community Builder',Park:'The Trailblazer'};
 return {archetype:done?(labels[category]||'The OneThing Climber'):'The First-Step Scout',evidence:done?`Your story leaned toward ${category}.`:'Every story starts somewhere.',description:done?'A little time became something you can point to. You kept giving your future self a useful head start.':'Your OneThing story is just getting started. One small quest will give it its first chapter.',quest_line:done?'Your completed quests made the highlight reel. OneThing saw you show up.':'The opening track is still yours to choose.',signature_move:done?`You kept finding your way back to ${skill||category}. Follow that thread into your next quest.`:'Start with a quest that fits the energy you have today.',plot_twist:done?'The small things were the story all along. Finishing one manageable action gave the next one somewhere to begin.':'You do not need a grand plan to begin. A small, finished action is a perfectly good plot twist.',onething_line:done?'You turned “I should do something” into “I did OneThing.” That is a habit worth keeping.':'Your next chapter only needs one thing.',next_step:skill?`Choose one manageable quest that builds on ${skill}.`:'Pick one short quest and take its first step.'};
}
function slidesFor(n){return [
 {label:'Your climbing alter ego',big:n.archetype,unit:n.evidence,body:n.description,color:'lime'},
 {label:'Your signature move',big:'A habit worth keeping.',body:n.signature_move,color:'purple'},
 {label:'The highlight reel',big:'You did the thing.',body:n.quest_line,color:'pink'},
 {label:'The plot twist',big:'Small was the secret.',body:n.plot_twist,color:'orange'},
 {label:'The OneThing effect',big:'Future you says thanks.',body:n.onething_line,color:'purple'},
 {label:'Your next chapter',big:'Leave room for more.',body:n.next_step,color:'lime'},
]}
function badgeMonth(timestamp){
 if(!timestamp)return '';
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit'}).formatToParts(new Date(timestamp)).map(part=>[part.type,part.value]));
 return `${parts.year}-${parts.month}`;
}
export default function Recap({data,onExplore}){
 const [period,setPeriod]=useState('lifetime'),[month,setMonth]=useState(data?.progress?.today?.slice(0,7)||new Date().toISOString().slice(0,7));
 const [year,setYear]=useState(data?.progress?.today?.slice(0,4)||String(new Date().getFullYear()));
 const [tab,setTab]=useState('story'),[slide,setSlide]=useState(0),[summary,setSummary]=useState(data),[result,setResult]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{
  let active=true;setSlide(0);setResult(null);setSummary(period==='lifetime'?data:null);setLoading(true);setError('');
  api.analytics(period==='month'?{period:'month',date:month+'-01'}:period==='year'?{period:'year',date:year+'-01-01'}:{}).then(value=>{if(active)setSummary(value)}).catch(e=>{if(active)setError(e.message)});
  api.recapNarrative({period,...(period==='month'?{month}:period==='year'?{year}:{})}).then(value=>{if(active){setResult(value);publishAchievements(value.badges)}}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});
  return()=>{active=false};
 },[period,month,year,data]);
 const story=result?.narrative||localStory(summary),slides=slidesFor(story),item=slides[slide],last=slide===slides.length-1;
 const badges=(result?.badges||data?.progress?.achievements||[]).map(badge=>({...badge,earned_in_period:badge.unlocked&&(period==='lifetime'||(period==='year'?badgeMonth(badge.earned_at).startsWith(year+'-'):badgeMonth(badge.earned_at)===month))}));
 function updateBadges(badges){const id=result?.recap_id;setResult(old=>old?.recap_id===id?{...old,badges}:old)}
 return <div className="recap-page">
  <div className="recap-heading"><span className="eyebrow">Your OneThing story · The climb, remembered.</span></div>
  <div className="recap-controls"><div className="period-tabs" role="group" aria-label="Recap period"><button aria-pressed={period==='lifetime'} onClick={()=>setPeriod('lifetime')}>Lifetime</button><button aria-pressed={period==='month'} onClick={()=>setPeriod('month')}>Monthly</button><button aria-pressed={period==='year'} onClick={()=>setPeriod('year')}>Yearly</button></div>{period==='month'&&<label>Recap month <input aria-label="Recap month" type="month" value={month} min="2000-01" max="2100-12" onChange={e=>/^\d{4}-\d{2}$/.test(e.target.value)&&setMonth(e.target.value)}/></label>}{period==='year'&&<label>Recap year <select aria-label="Recap year" value={year} onChange={e=>setYear(e.target.value)}>{Array.from({length:101},(_,i)=>String(2000+i)).map(value=><option key={value}>{value}</option>)}</select></label>}</div>
  <div className="recap-section-tabs" role="group" aria-label="Recap section"><button aria-pressed={tab==='story'} onClick={()=>setTab('story')}><Sparkles size={16}/> Your story</button><button aria-pressed={tab==='badges'} onClick={()=>setTab('badges')}><Award size={16}/> Badges</button><button aria-pressed={tab==='highlights'} onClick={()=>setTab('highlights')}>Highlights</button></div>
  {error&&<p role="alert" className="field-help">{error} Your recorded activity is still available in Progress.</p>}
  {tab==='badges'?<AchievementGallery badges={badges} monthly={period==='month'} periodLabel={period==='year'?'year':null}/>:tab==='highlights'?<RecapHighlights key={result?.recap_id||'pending'} result={result} onRecorded={updateBadges}/>:<>
   <p className="recap-scope">{period==='lifetime'?'Your whole journey':period==='year'?year:new Date(month+'-15T12:00:00').toLocaleDateString(undefined,{month:'long',year:'numeric'})}{loading?' · Writing your story…':result?.source==='gemini'?' · Written with Gemini':' · OneThing local story'}</p>
   {!summary?<p role="status">Loading this chapter…</p>:<ActivityWitness event={result?.source==='local'?'fallback_read':null} recapId={result?.recap_id} onRecorded={updateBadges}><section className={'wrapped recap-narrative '+item.color} aria-label="Progress recap">
    <div className="recap-dots">{slides.map((s,i)=><button key={s.label} aria-label={`Recap slide ${i+1}: ${s.label}`} aria-current={i===slide?'step':undefined} onClick={()=>setSlide(i)}/>)}</div>
    <span className="eyebrow">{item.label}</span>
    <div className="recap-big" aria-live="polite">{item.big}{item.unit&&<small>{item.unit}</small>}</div>
    <p className="recap-story">{item.body}</p>
    <div className="recap-navigation"><button disabled={slide===0} onClick={()=>setSlide(i=>i-1)}><ArrowLeft size={18}/> Back</button>{last?<button onClick={onExplore}>Find a quest <ArrowRight size={18}/></button>:<button onClick={()=>setSlide(i=>i+1)}>Next <ArrowRight size={18}/></button>}</div>
    <details className="recap-method"><summary>Behind this story</summary>This playful story uses every recorded quest in {period==='month'?'the selected month':period==='year'?'the selected year':'your lifetime history'}. It describes activity, not ability. {result?.source==='gemini'?'Gemini wrote this chapter.':'OneThing provides a local story while Gemini is unavailable or still writing.'} Badges are calculated from recorded activity and remain in your lifetime collection.</details>
   </section></ActivityWitness>}
  </>}
 </div>;
}
