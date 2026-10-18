import React,{useEffect,useState} from 'react';
import {ArrowRight,ArrowLeft,Sparkles,Award} from 'lucide-react';
import AchievementGallery from '../components/AchievementGallery';
import ActivityWitness,{publishAchievements} from '../components/ActivityWitness';
import RecapHighlights from '../components/RecapHighlights';
import {api} from '../api';

function localStory(data){
 const category=data?.top_category,skill=data?.top_skill,done=data?.completed_count||0;
 const labels={'General task':'The Small-Step Strategist','Online course':'The Skill Collector',Certification:'The Skill Collector',Class:'The Curious Scholar',Internship:'The Career Pathfinder',Job:'The Career Pathfinder',Networking:'The Connector',Club:'The Community Builder',Park:'The Trailblazer'};
 return {archetype:done?(labels[category]||'The OneThing Climber'):'The First-Step Scout',evidence:done?`Your story leaned toward ${category}.`:'Every story starts somewhere.',description:done?'A little time became something you can point to. You kept giving your future self a useful head start.':'Your OneThing story is just getting started. One small quest will give it its first chapter.',quest_line:done?'Your completed quests made the highlight reel. OneThing saw you show up.':'The opening track is still yours to choose.',signature_move:done?`You kept finding your way back to ${skill||category}. Follow that thread into your next quest.`:'Start with a quest that fits the energy you have today.',rhythm_line:done?`You showed up on ${data.active_days||1} day${data.active_days===1?'':'s'} in this chapter.`:'No streak yet. The first day of one is any day you choose.',plot_twist:done?'The small things were the story all along. Finishing one manageable action gave the next one somewhere to begin.':'You do not need a grand plan to begin. A small, finished action is a perfectly good plot twist.',onething_line:done?'You turned “I should do something” into “I did OneThing.” That is a habit worth keeping.':'Your next chapter only needs one thing.',next_step:skill?`Choose one manageable quest that builds on ${skill}.`:'Pick one short quest and take its first step.'};
}
const DAYS=['M','T','W','T','F','S','S'];
const plural=(n,word)=>`${n} ${word}${n===1?'':'s'}`;
// Grounded facts for the slides: the recap's own stats, or the period summary while the story loads.
function factsFor(stats,summary){
 if(stats)return stats;
 const s=summary||{},skills=Object.entries(s.skills||{}).sort((a,b)=>b[1]-a[1]).slice(0,3);
 return {completed_count:s.completed_count||0,points:s.points||0,minutes:s.estimated_minutes||0,active_days:s.active_days||0,top_category:s.top_category,top_skills:skills,category_count:Object.keys(s.categories||{}).length,badges_earned:0};
}
function Bars({rows}){const max=Math.max(1,...rows.map(r=>r[1]));return <ul className="recap-bars">{rows.map(([name,count])=><li key={name}><span>{name}</span><i style={{'--w':count/max}}/><b>{count}</b></li>)}</ul>}
function Week({counts}){const max=Math.max(1,...counts);return <div className="recap-week" role="img" aria-label={'Quests by weekday: '+counts.map((c,i)=>`${['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][i]} ${c}`).join(', ')}>{counts.map((c,i)=><span key={i} style={{'--h':c/max}} className={c===max?'peak':''}><i/>{DAYS[i]}</span>)}</div>}
function slidesFor(n,f,highlights){
 const done=f.completed_count>0,skill=f.top_skills?.[0]?.[0],tough=f.toughest_quest;
 const hours=f.minutes>=90?`${Math.round(f.minutes/6)/10} hrs`:`${f.minutes} min`;
 return [
 {label:'Your climbing alter ego',big:n.archetype,unit:n.evidence,body:n.description,color:'lime'},
 {label:'Your signature move',big:skill||f.top_category||'Your first move.',unit:skill?`Practiced ${plural(f.top_skills[0][1],'time')}`:null,visual:f.top_skills?.length>1&&<Bars rows={f.top_skills}/>,body:n.signature_move,color:'purple'},
 {label:'The highlight reel',big:done?plural(f.completed_count,'quest'):'Track one.',unit:done?'finished and recorded':null,visual:highlights?.length>0&&<ol className="recap-reel">{highlights.slice(0,3).map((h,i)=><li key={i}>{h.title}</li>)}</ol>,body:n.quest_line,color:'pink'},
 {label:'Your rhythm',big:f.busiest_weekday?`${f.busiest_weekday}s.`:done?plural(f.active_days,'active day'):'Any day.',unit:f.best_streak>1?`Best streak · ${f.best_streak} days`:f.busiest_day?.count>1?`${f.busiest_day.count} quests in one day`:null,visual:f.weekday_counts&&done&&<Week counts={f.weekday_counts}/>,body:n.rhythm_line,color:'orange'},
 {label:'The plot twist',big:tough&&['Hard','Challenging','Medium'].includes(tough.difficulty)?`${tough.difficulty} mode.`:f.category_count>1?`${f.category_count} paths.`:'Small was the secret.',visual:f.first_quest&&f.latest_quest&&f.first_quest.title!==(tough||f.latest_quest).title&&<div className="recap-arc"><span><small>Opened with</small>{f.first_quest.title}</span><span><small>{tough?`Toughest · ${tough.difficulty}`:'Latest'}</small>{(tough||f.latest_quest).title}</span></div>,body:n.plot_twist,color:'purple'},
 {label:'The OneThing effect',big:done?hours:'0 → 1',unit:done?'of small steps, estimated':null,visual:done&&<dl className="recap-stats"><div><dt>Points</dt><dd>{f.points}</dd></div><div><dt>Active days</dt><dd>{f.active_days}</dd></div><div><dt>{f.latest_badge?'New badges':'Kinds of work'}</dt><dd>{f.latest_badge?f.badges_earned:f.category_count}</dd></div></dl>,body:n.onething_line,color:'lime'},
 {label:'Your next chapter',big:skill?`More ${skill}.`:'Leave room for more.',unit:f.latest_badge?`Latest badge · ${f.latest_badge}`:null,body:n.next_step,color:'pink'},
]}
function badgeMonth(timestamp){
 if(!timestamp)return '';
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit'}).formatToParts(new Date(timestamp)).map(part=>[part.type,part.value]));
 return `${parts.year}-${parts.month}`;
}
export default function Recap({data,onExplore}){
 const [period,setPeriod]=useState('lifetime'),[month,setMonth]=useState(data?.progress?.today?.slice(0,7)||new Date().toISOString().slice(0,7));
 const [retry,setRetry]=useState(0),[now,setNow]=useState(Date.now());
 const [year,setYear]=useState(data?.progress?.today?.slice(0,4)||String(new Date().getFullYear()));
 const [tab,setTab]=useState('story'),[slide,setSlide]=useState(0),[summary,setSummary]=useState(data),[result,setResult]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{
  let active=true;setSlide(0);setResult(null);setSummary(period==='lifetime'?data:null);setLoading(true);setError('');
  api.analytics(period==='month'?{period:'month',date:month+'-01'}:period==='year'?{period:'year',date:year+'-01-01'}:{}).then(value=>{if(active)setSummary(value)}).catch(e=>{if(active)setError(e.message)});
  api.recapNarrative({period,...(period==='month'?{month}:period==='year'?{year}:{})}).then(value=>{if(active){setNow(Date.now());setResult(value);publishAchievements(value.badges)}}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});
  return()=>{active=false};
 },[period,month,year,data,retry]);
 useEffect(()=>{if(!result?.generation?.retry_at)return;const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer)},[result?.generation?.retry_at]);
 const retryWait=result?.generation?.retry_at?Math.max(0,Math.ceil((Date.parse(result.generation.retry_at)-now)/1000)):0;
 const story={...localStory(summary),...result?.narrative},slides=slidesFor(story,factsFor(result?.stats,summary),result?.highlights),item=slides[slide],last=slide===slides.length-1;
 const badges=(result?.badges||data?.progress?.achievements||[]).map(badge=>({...badge,earned_in_period:badge.unlocked&&(period==='lifetime'||(period==='year'?badgeMonth(badge.earned_at).startsWith(year+'-'):badgeMonth(badge.earned_at)===month))}));
 function updateBadges(badges){const id=result?.recap_id;setResult(old=>old?.recap_id===id?{...old,badges}:old)}
 return <div className="recap-page">
  <div className="recap-controls"><div className="period-tabs" role="group" aria-label="Recap period"><button aria-pressed={period==='lifetime'} onClick={()=>setPeriod('lifetime')}>Lifetime</button><button aria-pressed={period==='month'} onClick={()=>setPeriod('month')}>Monthly</button><button aria-pressed={period==='year'} onClick={()=>setPeriod('year')}>Yearly</button></div>{period==='month'&&<label>Recap month <input aria-label="Recap month" type="month" value={month} min="2000-01" max="2100-12" onChange={e=>/^\d{4}-\d{2}$/.test(e.target.value)&&setMonth(e.target.value)}/></label>}{period==='year'&&<label>Recap year <select aria-label="Recap year" value={year} onChange={e=>setYear(e.target.value)}>{Array.from({length:101},(_,i)=>String(2000+i)).map(value=><option key={value}>{value}</option>)}</select></label>}</div>
  <div className="recap-section-tabs" role="group" aria-label="Recap section"><button aria-pressed={tab==='story'} onClick={()=>setTab('story')}><Sparkles size={16}/> Your story</button><button aria-pressed={tab==='badges'} onClick={()=>setTab('badges')}><Award size={16}/> Badges</button><button aria-pressed={tab==='highlights'} onClick={()=>setTab('highlights')}>Highlights</button></div>
  {error&&<p role="alert" className="field-help">{error} Your recorded activity is still available in Progress.</p>}
  {!loading&&result?.source==='local'&&<aside className="recap-generation" role="status"><p>{result.generation?.message||'This request finished with a local story.'}</p>{result.generation?.retryable&&<button className="secondary" disabled={loading||retryWait>0} onClick={()=>setRetry(value=>value+1)}>{retryWait>0?`Retry in ${retryWait}s`:'Retry Gemini'}</button>}{result.generation?.status==='quota_exceeded'&&<a href="https://aistudio.google.com/usage" target="_blank" rel="noopener noreferrer">Check Gemini quota</a>}</aside>}
  {tab==='badges'?<AchievementGallery badges={badges} monthly={period==='month'} periodLabel={period==='year'?'year':null}/>:tab==='highlights'?<RecapHighlights key={result?.recap_id||'pending'} result={result} onRecorded={updateBadges}/>:<>
   <p className="recap-scope">{period==='lifetime'?'Your whole journey':period==='year'?year:new Date(month+'-15T12:00:00').toLocaleDateString(undefined,{month:'long',year:'numeric'})}{loading?' · Writing your story…':result?.source==='gemini'?' · Written with Gemini':' · OneThing local story'}</p>
   {!summary?<p role="status">Loading this chapter…</p>:<ActivityWitness event={result?.source==='local'?'fallback_read':null} recapId={result?.recap_id} onRecorded={updateBadges}><section className={'wrapped recap-narrative '+item.color} aria-label="Progress recap">
    <div className="recap-dots">{slides.map((s,i)=><button key={s.label} aria-label={`Recap slide ${i+1}: ${s.label}`} aria-current={i===slide?'step':undefined} onClick={()=>setSlide(i)}/>)}</div>
    <span className="eyebrow">{item.label}</span>
    <div className="recap-big" aria-live="polite">{item.big}{item.unit&&<small>{item.unit}</small>}</div>
    {item.visual||null}
    <p className="recap-story">{item.body}</p>
    <div className="recap-navigation"><button disabled={slide===0} onClick={()=>setSlide(i=>i-1)}><ArrowLeft size={18}/> Back</button>{last?<button onClick={onExplore}>Find a quest <ArrowRight size={18}/></button>:<button onClick={()=>setSlide(i=>i+1)}>Next <ArrowRight size={18}/></button>}</div>
    <details className="recap-method"><summary>Behind this story</summary>This playful story uses every recorded quest in {period==='month'?'the selected month':period==='year'?'the selected year':'your lifetime history'}. It describes activity, not ability. {loading?'Gemini is still writing. This is a local preview.':result?.source==='gemini'?'Gemini wrote this chapter.':'This request finished with a local story. See the generation status above for the reason.'} Badges are calculated from recorded activity and remain in your lifetime collection.</details>
   </section></ActivityWitness>}
  </>}
 </div>;
}
