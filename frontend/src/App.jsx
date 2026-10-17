import React, {useState, useEffect, useRef} from 'react';
import {ArrowRight, ArrowLeft, Bookmark, Check, Compass, Flag, Mountain, Sparkles, Sprout, Clock3, X, SlidersHorizontal, Pencil, Flame, ChevronDown, List, Image, Leaf, BookOpen, Users, Briefcase, Code2} from 'lucide-react';
import {api} from './api';
import MetadataFilters,{emptyMetadataFilters,metadataQuery} from './components/MetadataFilters';
import {durationLabel} from './utils/duration';
import Print from './components/Print';
import {photoFor} from './utils/photos';
import ResumeLab from './pages/ResumeLabPage';
import Recap from './pages/RecapPage';
import Analytics from './components/Analytics';
import StreakCalendar from './components/StreakCalendar';
import Onboarding from './components/Onboarding';
import Climb from './components/Climb';
import {crossedMilestone,climbPosition} from './utils/climbMath';
import {options,emptyPreferences,PreferenceFields} from './components/PreferenceFields';
import {chooseVariant,matchesOpportunity} from './utils/filtering';
import {mergeFeedPage,nextFeedOffset} from './utils/feedPaging';

const GOALS=['Explore my interests','Build my skills','Make an impact'];
const INTERESTS=['Design','Technology','Community','Sustainability','Arts'];
const SKILLS=['Writing','Coding','Research','Design'];
const SOURCES=['Class','Club','Certification','Local event','Networking','Job simulation','Internship','Creative project','Build challenge','Campus initiative'];
const NAV=[['Discover','Discover',Compass],['Saved things','Saved',Bookmark],['My progress','Progress',Mountain],['Resume lab','Resume',Pencil],['My recap','Recap',Sparkles]];
function imageFor(o){
 if(o.id==='green')return ['nature','A young plant growing on a green hillside'];
 if(['Class','Certification'].includes(o.kind))return ['learn','An open book and a little spark of inspiration'];
 if(['Club','Networking','Local event'].includes(o.kind))return ['community','Two people sharing ideas around a table'];
 if(o.kind==='Internship')return ['career','A satchel ready for a new career chapter'];
 if(o.id==='code')return ['build','A laptop with code and a handwritten checklist'];
 return ['creative','A sketchbook with colorful ideas and a pencil'];
}
// Hero image slot: the quest's graded scene photograph (utils/photos.js); the icon is only a fallback.
const CATEGORY_ICONS={nature:Leaf,learn:BookOpen,community:Users,career:Briefcase,build:Code2,creative:Pencil};
function Art({opportunity,osd}){const [name]=imageFor(opportunity);return <Print src={photoFor(opportunity)} color={opportunity.color} icon={CATEGORY_ICONS[name]} osd={osd}/>}
function Modal({title,onClose,children,className=''}){
 const ref=useRef(null),close=useRef(onClose);close.current=onClose;
 useEffect(()=>{
  const previous=document.activeElement;
  const controls=()=>Array.from(ref.current?.querySelectorAll('button:not(:disabled),select,input,textarea,a[href],[tabindex="0"]')||[]);
  controls()[0]?.focus();
  const keydown=e=>{
   if(e.key==='Escape'){e.preventDefault();close.current()}
   if(e.key==='Tab'){const items=controls(),first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}
  };
  document.addEventListener('keydown',keydown);
  return()=>{document.removeEventListener('keydown',keydown);previous?.focus()};
 },[]);
 return <div className="overlay"><section ref={ref} className={`modal ${className}`} role="dialog" aria-modal="true" aria-label={title}><div className="sheet-handle"/><div className="modal-heading"><span>{title}</span><button className="icon-button" onClick={onClose} aria-label={`Close ${title}`}><X size={20}/></button></div>{children}</section></div>
}
function ChoiceList({label,choices,value,onChange}){return <fieldset><legend>{label}</legend><div className="choice-tags">{choices.map(v=><button type="button" key={v} aria-pressed={value.includes(v)} onClick={()=>onChange(value.includes(v)?value.filter(x=>x!==v):[...value,v])}>{value.includes(v)&&<Check size={13}/>} {v}</button>)}</div></fieldset>}
export default function App(){
 const [climbFrom,setClimbFrom]=useState(null);
 const [page,setPage]=useState('Discover'),[data,setData]=useState(null),[quests,setQuests]=useState([]),[progress,setProgress]=useState({points:0,completed_count:0,saved_count:0,activity:[]}),[analytics,setAnalytics]=useState(null);
 const [opening,setOpening]=useState(true),[error,setError]=useState(''),[busy,setBusy]=useState(false),[detail,setDetail]=useState(null),[active,setActive]=useState(null),[checked,setChecked]=useState([]),[reward,setReward]=useState(null),[filtersOpen,setFiltersOpen]=useState(false),[calendarOpen,setCalendarOpen]=useState(false);
 const [goal,setGoal]=useState(GOALS[0]),[interests,setInterests]=useState(['Software Engineering','Web & App Development']),[skills,setSkills]=useState(['Writing']),[mood,setMood]=useState('Okay'),[effort,setEffort]=useState('small');
 const [goals,setGoals]=useState([]),[preferences,setPreferences]=useState({...emptyPreferences}),[listView,setListView]=useState(()=>localStorage.getItem('one-thing-view')==='list');
 const [difficulty,setDifficulty]=useState('Any'),[kinds,setKinds]=useState([]),[mode,setMode]=useState('Anywhere'),[goalFilter,setGoalFilter]=useState('Any goal'),[skillFilter,setSkillFilter]=useState('Any skill'),[interestFilter,setInterestFilter]=useState('Any interest'),[gapSkills,setGapSkills]=useState([]);
 const [metadata,setMetadata]=useState({...emptyMetadataFilters});
 const initialized=useRef(false),feedRef=useRef(null),feedVersion=useRef(0),coordinates=useRef(null),endOfFeedRef=useRef(null),feedRequest=useRef(null),feedData=useRef(null);
 const [savedRows,setSavedRows]=useState([]),[feedLoading,setFeedLoading]=useState(false),[feedError,setFeedError]=useState('');
 async function feedFilters(){
  const filters={...metadataQuery(metadata),interests,goals,challenges:preferences.challenges,time:preferences.time,locations:preferences.locations,commitment:preferences.commitment,step_size:difficulty,kind:kinds,skills:gapSkills,limit:40};
  if(preferences.locations.includes('Near me')){
   if(!coordinates.current){
    if(!navigator.geolocation)throw new Error('Location is unavailable. Choose another location filter.');
    coordinates.current=await new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(p=>resolve({lat:p.coords.latitude,lon:p.coords.longitude}),()=>reject(new Error('Allow location access for Near me, or choose another location filter.')),{timeout:10000,maximumAge:300000}));
   }
   Object.assign(filters,coordinates.current,{radius_km:25});
  }
  return filters;
 }
 async function fetchFeed(append=false){
  if(append&&(feedRequest.current!==null||!feedData.current?.has_more))return null;
  const version=++feedVersion.current;feedRequest.current=version;setFeedLoading(true);setFeedError('');
  try{
   const filters=await feedFilters();
   if(version!==feedVersion.current)return null;
   const f=await api.feed({...filters,offset:append?nextFeedOffset(feedData.current):0});
   if(version!==feedVersion.current)return null;
   if(append&&f.has_more&&!f.opportunities.length)throw new Error('The next page was empty. Try loading it again.');
   const merged=mergeFeedPage(append?feedData.current:null,{...f,page_count:f.opportunities.length});
   feedData.current=merged;setData(merged);
   setQuests(old=>[...new Map([...old,...f.quests].map(q=>[q.id,q])).values()]);return f;
  }catch(e){if(version===feedVersion.current&&append)setFeedError(e.message);throw e}
  finally{if(version===feedVersion.current){feedRequest.current=null;setFeedLoading(false)}}
 }
 async function load(refreshFeed=true){
  const [f,s,p,a]=await Promise.all([refreshFeed?fetchFeed():Promise.resolve(data),api.saved(),api.progress(),api.analytics()]);
  if(!f)return;if(!refreshFeed){const ids=new Set(s.opportunities.map(o=>o.id));setData(old=>{const updated={...old,opportunities:old.opportunities.map(o=>({...o,saved:ids.has(o.id)}))};feedData.current=updated;return updated})}setSavedRows(s.opportunities);setQuests(old=>[...new Map([...old,...f.quests,...s.quests].map(q=>[q.id,q])).values()]);setProgress(p);setAnalytics(a);
  if(!initialized.current){if(f.profile){setGoal(f.profile.goal);setInterests(f.profile.interests.filter(t=>options.interests.includes(t)).slice(0,3));setGoals((f.profile.goals||[]).slice(0,3));setPreferences({...emptyPreferences,...f.profile.preferences});setSkills(f.profile.skills)}if(f.checkin){setMood(f.checkin.mood);setEffort(f.checkin.effort)}initialized.current=true}
 }
 useEffect(()=>{load().catch(e=>setError(e.message))},[]);
 useEffect(()=>{if(opening||filtersOpen)return;++feedVersion.current;feedRequest.current=null;setFeedLoading(true);setFeedError('');const timer=setTimeout(()=>{setError('');fetchFeed().catch(e=>setError(e.message))},150);return()=>clearTimeout(timer)},[opening,filtersOpen,JSON.stringify([interests,goals,preferences,difficulty,kinds,gapSkills,metadata])]);
 async function action(fn){setBusy(true);setError('');try{await fn()}catch(e){setError(e.message)}finally{setBusy(false)}}
 function resetFilters(){setMetadata({...emptyMetadataFilters});setInterests([]);setGoals([]);setPreferences({...emptyPreferences});setDifficulty('Any');setKinds([]);setMode('Anywhere');setGoalFilter('Any goal');setSkillFilter('Any skill');setInterestFilter('Any interest');setGapSkills([])}
 function navigate(next){setPage(next);setError('')}
 async function toggleSave(o){if(o.saved)await api.unsave(o.id);else await api.save(o.id);await load(false)}
 const all=(page==='Saved things'?savedRows:(data?.opportunities||[])).map(o=>{
  const variant=chooseVariant(o,quests,{stepSize:difficulty,preferences,defaultEffort:data?.checkin?.effort||'small'});
  return variant?{...o,minutes:variant.minutes,suggested_quest_id:variant.id,difficulty:o.personalization&&!o.sample?o.difficulty:variant.difficulty,preparation_difficulty:variant.difficulty,effort:variant.effort,size:variant.size,hasVariant:true}:{...o,hasVariant:false};
 });
 const visible=all.filter(o=>page==='Saved things'?o.saved:o.hasVariant&&(data?.data_mode==='catalog'||matchesOpportunity(o,{interests,goals,preferences})&&(!kinds.length||kinds.includes(o.kind))&&(!gapSkills.length||o.skills?.some(t=>gapSkills.includes(t)))));
 const selected=detail?all.find(o=>o.id===detail):null;
 const selectedQuest=selected&&(quests.find(q=>q.id===selected.suggested_quest_id)||quests.find(q=>q.opportunity_id===selected.id));
 const filterCount=(difficulty!=='Any')+interests.length+goals.length+preferences.challenges.length+preferences.time.length+preferences.locations.length+(preferences.commitment!=='A mix of both')+kinds.length+gapSkills.length+Object.keys(metadataQuery(metadata)).length;
 const modalOpen=!!(detail||active||reward!==null||filtersOpen||calendarOpen);
 const loadMoreRef=useRef(null);loadMoreRef.current=()=>fetchFeed(true);
 useEffect(()=>{
  const root=feedRef.current,target=endOfFeedRef.current;
  if(opening||page!=='Discover'||modalOpen||feedLoading||feedError||!data?.has_more||!root||!target||!('IntersectionObserver' in window))return;
  const observer=new IntersectionObserver(entries=>{
   if(entries.some(entry=>entry.isIntersecting)&&feedRequest.current===null)loadMoreRef.current().catch(()=>{});
  },{root,rootMargin:'0px 0px 240px 0px',threshold:0});
  observer.observe(target);return()=>observer.disconnect();
 },[opening,page,modalOpen,feedLoading,feedError,data?.has_more,data?.opportunities.length,listView]);
 async function startQuest(){if(!selected.saved){await api.save(selected.id);await load(false)}setDetail(null);setActive(selectedQuest);setChecked([])}
 function nextCard(e){const card=e.currentTarget.closest('article'),sibling=card.nextElementSibling,next=sibling?.tagName==='ARTICLE'||data?.has_more?sibling:card.parentElement.firstElementChild;card.parentElement.scrollTo({top:next.offsetTop-card.parentElement.firstElementChild.offsetTop,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}
 const errorBox=error&&<div role="alert" className="error"><span>{error}</span><button type="button" disabled={busy} onClick={()=>action(load)}>Retry</button></div>;

 const topPick=visible[0];
 const topQuest=topPick&&(quests.find(q=>q.id===topPick.suggested_quest_id)||quests.find(q=>q.opportunity_id===topPick.id));
 const sample=(data?.opportunities||[]).find(o=>o.id==='sample-networking-backend')||all[0];
 async function saveOnboarding(){let ok=false;await action(async()=>{await api.profile({goal:goals[0]||GOALS[0],goals,interests,skills,preferences});await load();ok=true});return ok}
 // No match for the exact onboarding mix (catalog filters are strict: every choice must match): keep the first
 // interest, drop goals and places, then open the feed.
 async function widenOnboarding(){const prefs={...preferences,locations:[]},keep=interests.slice(0,1);await action(async()=>{await api.profile({goal:GOALS[0],goals:[],interests:keep,skills,preferences:prefs});setGoals([]);setInterests(keep);setPreferences(prefs);enterApp()})}
 function enterApp(){setOpening(false);setKinds([]);setGapSkills([]);setPage('Discover')}
 if(opening)return <Onboarding data={data} busy={busy} error={error} hasProfile={!!data?.profile} interests={interests} setInterests={setInterests} goals={goals} setGoals={setGoals} skills={skills} setSkills={setSkills} preferences={preferences} setPreferences={setPreferences} stepSize={difficulty} setStepSize={setDifficulty} sample={sample} topPick={topPick} topQuest={topQuest} onSave={saveOnboarding} onEnter={enterApp} onWiden={widenOnboarding} onSkip={()=>action(async()=>{if(!data.profile){await api.profile({goal:GOALS[0],interests:['Design','Community'],skills:['Writing']});await load()}resetFilters();enterApp()})}/>;

 return <div className="phone-shell"><div className="app-surface" inert={modalOpen?true:undefined}><header className="app-header"><a className="brand" href="#" onClick={e=>{e.preventDefault();navigate('Discover')}}>OneThing</a><div className="header-actions">{progress.demo_clock?.simulated&&<button className="demo-date-badge" onClick={()=>navigate('My progress')}>Demo · {progress.today}</button>}<button className="streak-chip" aria-label={`View streak calendar, ${progress.streak||0} day streak`} onClick={()=>setCalendarOpen(true)}><Flame size={15}/>{progress.streak||0}</button></div></header>
 {errorBox}
 <main className={['Discover','Saved things'].includes(page)?'feed-page':'page-scroll'} key={page}>
 {['Discover','Saved things'].includes(page)?<><div className="feed-heading"><div><span className="eyebrow">{page==='Discover'?'A LITTLE LESS SCROLL. A LITTLE MORE YOU.':'YOUR NEXT STEPS, KEPT CLOSE.'}</span><h1>{page==='Discover'?<>For <em>you.</em></>:<>Saved <em>things.</em></>}</h1></div><span className="feed-total">{page==='Saved things'?visible.length:(data?.total??visible.length)} {data?.data_mode==='sample'?'samples':'opportunities'}</span></div>
 <div className={listView?'opportunity-list':'opportunity-feed'} ref={feedRef} tabIndex={0} role="region" aria-label={listView?'Text-only opportunity list':'Opportunity feed. Swipe or scroll to explore.'} key={page+JSON.stringify([difficulty,kinds,interests,goals,preferences,gapSkills,data?.checkin?.effort,listView])}>
 {visible.map((o,index)=><article className={`feed-card ${o.color}`} key={o.id}><button className="card-open" aria-label={`View details: ${o.title}`} onClick={()=>{setError('');setDetail(o.id)}}><div className="card-description"><span className="card-kicker">{o.kind} <span>· {o.mode} · {o.size||'Small'} step</span></span><h2>{o.title}</h2><p>{o.description}</p></div>{!listView&&<div className="card-image"><Art opportunity={o} osd={`00:${String(o.minutes||0).padStart(2,'0')}:00`}/><span className="image-note">a little possibility, just for you</span></div>}<div className="card-bottom"><span>{o.sample?'SAMPLE OPPORTUNITY':`CACHED: ${o.source}`}</span><span>Tap anywhere for details <ArrowRight size={13}/></span></div></button><button className={`save-float ${o.saved?'is-saved':''}`} aria-label={`${o.saved?'Unsave':'Save'} ${o.title}`} aria-pressed={o.saved} disabled={busy} onClick={()=>action(()=>toggleSave(o))}><Bookmark size={21} fill={o.saved?'currentColor':'none'}/></button>{!o.sample&&o.source_url&&<a className="opportunity-source-link" href={o.source_url} target="_blank" rel="noopener noreferrer" aria-label={`View original opportunity: ${o.title} (opens in a new tab)`}>View opportunity<ArrowRight size={14}/></a>}{!listView&&<div className="feed-pagination"><span>{String(index+1).padStart(2,'0')} / {String(visible.length).padStart(2,'0')}</span><button aria-label={index===visible.length-1?(data?.has_more?'Continue to more opportunities':'Return to first opportunity'):'Next opportunity'} onClick={nextCard}>{index===visible.length-1?(data?.has_more?'More possibilities below':'Back to the start'):'Scroll for another little thing'} <ChevronDown size={14}/></button></div>}</article>)}
 {!visible.length&&!feedLoading&&<div className="empty"><Sprout size={32}/><h2>{page==='Saved things'?'Keep a little possibility.':'A fresh direction?'}</h2><p>{page==='Saved things'?'Tap a bookmark while exploring to save an opportunity here.':'No opportunities match this mix. Try clearing a filter.'}</p><button className="primary" onClick={()=>{resetFilters();navigate('Discover')}}>{page==='Saved things'?'Explore opportunities':'Reset my filters'}<ArrowRight size={16}/></button></div>}
 {page==='Discover'&&<div ref={endOfFeedRef} className="feed-load-sentinel" aria-busy={feedLoading}>
 {feedLoading&&<p role="status" className="feed-loading"><span className="feed-loading-dot"/>Finding your next possibilities…</p>}
 {feedError?<div className="feed-load-error" role="alert"><p>{feedError}</p><button className="secondary" disabled={feedLoading} onClick={()=>{fetchFeed(true).catch(()=>{})}}>Try loading more again</button></div>:data?.has_more&&!feedLoading?<button className="text-link" onClick={()=>{fetchFeed(true).catch(()=>{})}}>Load more opportunities<ArrowRight size={15}/></button>:!feedLoading&&visible.length>0?<p className="fictional-note">You've reached the end of this selection.</p>:null}
 </div>}</div></>:<><div className="page-heading"><span className="eyebrow">ONE THING AT A TIME</span><h1>{page==='My progress'?<>Your little <em>climb.</em></>:page==='Resume lab'?<>Your next <em>chapter.</em></>:<>Your progress.<br/><em>In full color.</em></>}</h1></div>
 {page==='Resume lab'?<ResumeLab onExplore={gaps=>{resetFilters();setGapSkills(gaps);navigate('Discover')}}/>:page==='My recap'?<Recap data={analytics} onExplore={()=>{resetFilters();navigate('Discover')}}/>:<><div className="progress-summary"><button className="streak-chip" aria-label="View streak calendar" onClick={()=>setCalendarOpen(true)}><Flame size={16}/>{progress.streak||0} day streak</button><p>{progress.active_today?"Today's little step is done. See you tomorrow.":'One completed quest today keeps your climb going.'}</p><small>Best: {progress.longest_streak||0} days · Pacific time</small></div><Climb progress={progress} fromPoints={climbFrom}/><section className="progress-panel"><div className="stats"><div><strong>{progress.completed_count}</strong><span>quests completed</span></div><div><strong>{progress.saved_count}</strong><span>things saved</span></div></div><h2>Your little wins</h2>{progress.activity.length?progress.activity.map(a=><div className="activity" key={a.id||a.quest_id}><span className="tick"><Check size={17}/></span><div><strong>{a.title}</strong><small>{new Date(a.completed_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})} · Quest completed</small></div><b>+{a.points}</b></div>):<p className="field-help">Your first win is waiting. Complete a quest to start your trail.</p>}</section><Analytics today={progress.today} clock={progress.demo_clock} onDateChange={async value=>{await api.demoDate(value);await load();}} data={analytics} onRecap={()=>navigate('My recap')}/></>}
 <p className="fictional-note">Made for your in-between moments. One thing at a time.</p></>}
 </main>
 {['Discover','Saved things'].includes(page)&&<div className="feed-toolbar"><button className="view-toggle" aria-label={listView?'Switch to image feed':'Switch to text-only list'} aria-pressed={listView} onClick={()=>{const next=!listView;setListView(next);localStorage.setItem('one-thing-view',next?'list':'images')}}>{listView?<Image size={17}/>:<List size={17}/>}<span>{listView?'Images':'List'}</span></button>{page==='Discover'&&<button onClick={()=>setFiltersOpen(true)}><SlidersHorizontal size={17}/>Filters{filterCount>0&&<span className="filter-count">{filterCount}</span>}</button>}</div>}
 <nav className="bottom-nav" aria-label="Main navigation">{NAV.map(([value,label,Icon])=><button key={value} className={page===value?'active':''} aria-current={page===value?'page':undefined} onClick={()=>navigate(value)}><span className="nav-icon"><Icon size={21}/>{value==='Saved things'&&progress.saved_count>0&&<span className="nav-count">{progress.saved_count}</span>}</span><span>{label}</span></button>)}</nav></div>
 {calendarOpen&&<Modal title="Your streak calendar" onClose={()=>setCalendarOpen(false)}><StreakCalendar progress={progress}/></Modal>}
 {filtersOpen&&<Modal title="Your kind of things" onClose={()=>setFiltersOpen(false)} className="filter-sheet"><h2>A little more <em>you.</em></h2><p>Every chosen interest, goal, and skill must match. Difficulty and time choices let you select a range. Choose fewer interests or goals for more results.</p><div className="feed-filters"><label>Step size<select aria-label="Step size" value={difficulty} onChange={e=>setDifficulty(e.target.value)}>{['Any','Small','Medium','Big'].map(v=><option key={v}>{v}</option>)}</select></label></div><PreferenceFields interests={interests} setInterests={setInterests} goals={goals} setGoals={setGoals} preferences={preferences} setPreferences={setPreferences}/><ChoiceList label="Opportunity types · none selected means all" choices={data?.kinds||SOURCES} value={kinds} onChange={setKinds}/>{data?.data_mode==='catalog'&&<MetadataFilters value={metadata} onChange={setMetadata}/>}{gapSkills.length>0&&<p className="gap-filter">Resume keywords to explore: {gapSkills.join(', ')} <button onClick={()=>setGapSkills([])}>Clear</button></p>}{errorBox}<div className="sheet-actions"><button className="text-link" onClick={resetFilters}>Reset filters</button><button className="primary" disabled={busy||!skills.length} onClick={()=>action(async()=>{await api.profile({goal:goals[0]||GOALS[0],goals,interests,skills,preferences});await load();setFiltersOpen(false)})}>Apply filters<ArrowRight size={16}/></button></div></Modal>}
 {selected&&<Modal title="A little more detail" onClose={()=>setDetail(null)} className="detail-sheet"><div className="detail-image"><Art opportunity={selected}/></div><span className="eyebrow">{selected.sample?'FICTIONAL SAMPLE':'CACHED SOURCE RECORD'} · {selected.kind.toUpperCase()}</span><h2>{selected.title}</h2><p>{selected.description}</p>{!selected.sample&&<p><a href={selected.source_url} target="_blank" rel="noopener noreferrer">View opportunity (original source)</a></p>}<p className="provider">{selected.organization} · {selected.mode}</p><div className="opportunity-facts">{selected.personalization&&<><p><strong>Opportunity challenge (estimated)</strong>{selected.personalization.challenge_levels.join(", ")}<small>{selected.personalization.assessment?.difficulty_basis}</small></p><p><strong>Full opportunity duration</strong>{durationLabel(selected.personalization.duration)}<small>{selected.personalization.duration.basis}</small></p></>}{selected.personalization?.assessment&&<><p><strong>Experience (estimated)</strong>{selected.personalization.assessment.experience_level}</p><p><strong>Cost</strong>{selected.personalization.assessment.cost}</p><p><strong>Prerequisites</strong>{selected.personalization.assessment.prerequisite_status}<small>{selected.personalization.assessment.prerequisite_basis}</small></p><p><strong>Schedule</strong>{selected.personalization.assessment.schedule_type}</p></>}{selected.location&&<p><strong>Where</strong>{selected.location}</p>}{selected.commitment&&<p><strong>Full opportunity commitment</strong>{selected.commitment}</p>}{selected.requirements?.length>0&&<div><strong>Who it suits</strong><ul>{selected.requirements.map(r=><li key={r}>{r}</li>)}</ul></div>}</div><div className="tags">{selected.tags.map(t=><span key={t}>{t}</span>)}</div><div className="match"><Sparkles size={16}/><span>{selected.matching_tags.length?`Matches your ${selected.matching_tags.join(', ')} interests and skills.`:'A new direction you might enjoy exploring.'}</span></div>{selectedQuest&&<div className="quest-preview"><span className="eyebrow">YOUR FIRST STEP</span><h3>{selectedQuest.title}</h3><p>{selectedQuest.description}</p><div className="quest-meta"><span>{selectedQuest.size||'Medium'} step</span><span>{selectedQuest.minutes} min (estimated)</span><span>+{selectedQuest.points} points</span></div></div>}{errorBox}<div className="sheet-actions"><button className="secondary" disabled={busy} aria-pressed={selected.saved} onClick={()=>action(()=>toggleSave(selected))}><Bookmark size={17} fill={selected.saved?'currentColor':'none'}/>{selected.saved?'Unsave':'Save for later'}</button><button className="primary" disabled={busy||!selectedQuest} onClick={()=>action(startQuest)}>{selectedQuest?.completed?'View completed quest':'Open my quest'}<ArrowRight size={16}/></button></div><p className="fictional-note">{selected.sample?'A fictional opportunity for practice.':<>Collected {new Date(selected.collected_at).toLocaleDateString()}. {selected.availability} Verify current details and any estimated difficulty at the source.</>}</p></Modal>}
 {active&&<Modal title="Your little first step" onClose={()=>setActive(null)} className="quest-sheet"><h2>{active.title}</h2><div className="quest-meta"><span>{active.size||'Medium'} step</span><span>{active.minutes} min (estimated)</span><span>+{active.points} points</span>{active.daily&&<span>Daily practice</span>}</div><p>{active.description}</p><div className="checklist">{active.steps.map((step,i)=><label key={step}><input type="checkbox" checked={checked.includes(i)} onChange={()=>setChecked(checked.includes(i)?checked.filter(x=>x!==i):[...checked,i])}/><span>{step}</span></label>)}</div>{errorBox}<button className="primary wide" disabled={busy||active.completed||checked.length!==active.steps.length} onClick={()=>action(async()=>{const before=progress.points;const result=await api.complete(active.id);setClimbFrom(result.points_earned>0?before:null);await load(false);setActive(null);setReward(result.points_earned)})}>{active.completed?'Already completed':busy?'Saving your step…':'I did my one thing'}<Check size={18}/></button><p className="fictional-note">Take your time and do the steps offline. Completion is self-reported.</p></Modal>}
 {reward!==null&&<Modal title="A little win" onClose={()=>setReward(null)} className="celebration">{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)&&<div className="milestone-confetti" aria-hidden="true">{Array.from({length:12},(_,i)=><i key={i} style={{'--i':i}}/>)}</div>}<Climb progress={progress} fromPoints={climbFrom}/><span className="eyebrow">{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)?'A NEW MILESTONE, JUST FOR YOU':'LOOK AT YOU, MOVING FORWARD'}</span><h2>{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)?<>Level {climbPosition(progress.points).level}.<br/><em>Look how far you've come.</em></>:<>Small step.<br/><em>Real progress.</em></>}</h2><p>You turned a little time into something good.</p><div className="reward-points">+{reward}<span>points for your journey</span></div><button className="primary wide" onClick={()=>{setReward(null);navigate('My progress')}}>See my climb<ArrowRight size={18}/></button><button className="text-link" onClick={()=>setReward(null)}>Keep exploring</button></Modal>}
 </div>;
}
