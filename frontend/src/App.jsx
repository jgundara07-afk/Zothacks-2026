import React, {useState, useEffect, useRef} from 'react';
import {ArrowRight, ArrowLeft, Bookmark, Check, Compass, Flag, Mountain, Sparkles, Sprout, Clock3, X, SlidersHorizontal, Pencil, Flame, ChevronDown, List, Image, Leaf, BookOpen, Users, Briefcase, Code2, UserRound} from 'lucide-react';
import {api} from './api';
import ProfileEditor from './components/ProfileEditor';
import MetadataFilters,{emptyMetadataFilters,metadataQuery} from './components/MetadataFilters';
import {durationLabel} from './utils/duration';
import Print from './components/Print';
import {photoFor,photosForList} from './utils/photos';
import {simpleTitle,subline,kindLabel,blurb} from './utils/titles';
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
const NAV=[['Discover','Discover',Compass],['Saved things','Saved',Bookmark],['My progress','Progress',Mountain],['My recap','Recap',Sparkles]];
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
function Art({opportunity,osd,src}){const [name]=imageFor(opportunity);return <Print src={src||photoFor(opportunity)} color={opportunity.color} icon={CATEGORY_ICONS[name]} osd={osd}/>}
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
 const [displayName,setDisplayName]=useState('');
 const [profileOpen,setProfileOpen]=useState(false),[profileRevision,setProfileRevision]=useState(0);
 const [page,setPage]=useState('Discover'),[data,setData]=useState(null),[quests,setQuests]=useState([]),[progress,setProgress]=useState({points:0,completed_count:0,saved_count:0,activity:[]}),[analytics,setAnalytics]=useState(null);
 const [opening,setOpening]=useState(true),[error,setError]=useState(''),[busy,setBusy]=useState(false),[detail,setDetail]=useState(null),[active,setActive]=useState(null),[checked,setChecked]=useState([]),[reward,setReward]=useState(null),[filtersOpen,setFiltersOpen]=useState(false),[calendarOpen,setCalendarOpen]=useState(false);
 const [goal,setGoal]=useState(GOALS[0]),[interests,setInterests]=useState(['Software Engineering','Web & App Development']),[skills,setSkills]=useState(['Writing']),[mood,setMood]=useState('Okay'),[effort,setEffort]=useState('small');
 const [goals,setGoals]=useState([]),[preferences,setPreferences]=useState({...emptyPreferences}),[listView,setListView]=useState(()=>localStorage.getItem('one-thing-view')==='list');
 const [difficulty,setDifficulty]=useState('Any'),[kinds,setKinds]=useState([]),[mode,setMode]=useState('Anywhere'),[goalFilter,setGoalFilter]=useState('Any goal'),[skillFilter,setSkillFilter]=useState('Any skill'),[interestFilter,setInterestFilter]=useState('Any interest');
 const [metadata,setMetadata]=useState({...emptyMetadataFilters});
 const initialized=useRef(false),feedRef=useRef(null),feedVersion=useRef(0),coordinates=useRef(null),endOfFeedRef=useRef(null),feedRequest=useRef(null),feedData=useRef(null),relatedFeed=useRef(false);
 const [savedRows,setSavedRows]=useState([]),[feedLoading,setFeedLoading]=useState(false),[feedError,setFeedError]=useState('');
 async function feedFilters(){
  const filters={...metadataQuery(metadata),interests,goals,challenges:preferences.challenges,time:preferences.time,locations:preferences.locations,commitment:preferences.commitment,step_size:difficulty,kind:kinds,limit:40};
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
   let f=await (relatedFeed.current?api.recommendations({step_size:difficulty,limit:40,offset:append?nextFeedOffset(feedData.current):0}):api.feed({...filters,offset:append?nextFeedOffset(feedData.current):0}));
   if(opening&&!append&&!f.opportunities.length&&!f.fallback?.recommendation){relatedFeed.current=true;f=await api.recommendations({step_size:difficulty,limit:40});}
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
  if(!initialized.current){if(f.profile){setGoal(f.profile.goal);setInterests(f.profile.interests.filter(t=>options.interests.includes(t)).slice(0,options.max_selected_interests));setGoals((f.profile.goals||[]).slice(0,3));setPreferences({...emptyPreferences,...f.profile.preferences});setSkills(f.profile.skills)}if(f.checkin){setMood(f.checkin.mood);setEffort(f.checkin.effort)}initialized.current=true}
 }
 useEffect(()=>{load().catch(e=>setError(e.message))},[]);
 useEffect(()=>{if(opening||filtersOpen)return;++feedVersion.current;feedRequest.current=null;setFeedLoading(true);setFeedError('');const timer=setTimeout(()=>{setError('');fetchFeed().catch(e=>setError(e.message))},150);return()=>clearTimeout(timer)},[opening,filtersOpen,profileRevision,JSON.stringify([interests,goals,preferences,difficulty,kinds,metadata])]);
 async function action(fn){setBusy(true);setError('');try{await fn()}catch(e){setError(e.message)}finally{setBusy(false)}}
 function resetFilters(){setMetadata({...emptyMetadataFilters});setInterests([]);setGoals([]);setPreferences({...emptyPreferences});setDifficulty('Any');setKinds([]);setMode('Anywhere');setGoalFilter('Any goal');setSkillFilter('Any skill');setInterestFilter('Any interest')}
 function navigate(next){setPage(next);setError('')}
 async function toggleSave(o){if(o.saved)await api.unsave(o.id);else await api.save(o.id);await load(false)}
 const all=(page==='Saved things'?savedRows:(data?.opportunities||[])).map(o=>{
  const variant=chooseVariant(o,quests,{stepSize:difficulty,preferences,defaultEffort:data?.checkin?.effort||'small'});
  return variant?{...o,minutes:variant.minutes,suggested_quest_id:variant.id,difficulty:o.personalization&&!o.sample?o.difficulty:variant.difficulty,preparation_difficulty:variant.difficulty,effort:variant.effort,size:variant.size,hasVariant:true}:{...o,hasVariant:false};
 });
 const visible=all.filter(o=>page==='Saved things'?o.saved:o.hasVariant&&(data?.data_mode==='catalog'||matchesOpportunity(o,{interests,goals,preferences})&&(!kinds.length||kinds.includes(o.kind))));
 const feedPhotos=photosForList(visible);
 const selected=detail?all.find(o=>o.id===detail):null;
 const selectedQuest=selected&&(quests.find(q=>q.id===selected.suggested_quest_id)||quests.find(q=>q.opportunity_id===selected.id));
 const filterCount=(difficulty!=='Any')+interests.length+goals.length+preferences.challenges.length+preferences.time.length+preferences.locations.length+(preferences.commitment!=='A mix of both')+kinds.length+Object.keys(metadataQuery(metadata)).length;
 const modalOpen=!!(profileOpen||detail||active||reward!==null||filtersOpen||calendarOpen);
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
 async function saveOnboarding(){relatedFeed.current=false;let ok=false;await action(async()=>{await api.profile({goal:goals[0]||GOALS[0],goals,interests,skills,preferences});await load();ok=true});return ok}
 // If even neutral alternatives cannot fit the current constraints, explicitly keep the first
 // interest, drop goals and places, then open the feed.
 async function widenOnboarding(){const prefs={...preferences,locations:[]},keep=interests.slice(0,1);await action(async()=>{await api.profile({goal:GOALS[0],goals:[],interests:keep,skills,preferences:prefs});setGoals([]);setInterests(keep);setPreferences(prefs);enterApp()})}
 function enterApp(){setOpening(false);setKinds([]);setPage('Discover')}
 if(opening)return <Onboarding onLogin={setDisplayName} data={data} busy={busy} error={error} hasProfile={!!data?.profile} interests={interests} setInterests={setInterests} goals={goals} setGoals={setGoals} skills={skills} setSkills={setSkills} preferences={preferences} setPreferences={setPreferences} stepSize={difficulty} setStepSize={setDifficulty} sample={sample} topPick={topPick} topQuest={topQuest} onSave={saveOnboarding} onEnter={enterApp} onWiden={widenOnboarding} onSkip={()=>action(async()=>{if(!data.profile){await api.profile({goal:GOALS[0],interests:['Design','Community'],skills:['Writing']});await load()}resetFilters();enterApp()})}/>;

 return <div className="phone-shell"><div className="app-surface" inert={modalOpen?true:undefined}><header className="app-header"><a className="brand" href="#" onClick={e=>{e.preventDefault();navigate('Discover')}}>OneThing</a><div className="header-actions">{progress.demo_clock?.simulated&&<button className="demo-date-badge" onClick={()=>navigate('My progress')}>Demo Â· {progress.today}</button>}<button className="streak-chip" aria-label={`View streak calendar, ${progress.streak||0} day streak`} onClick={()=>setCalendarOpen(true)}><Flame size={15}/>{progress.streak||0}</button><button className="profile-button" aria-label="Edit profile" onClick={()=>{setError('');setProfileOpen(true)}}><UserRound size={17}/><span>{displayName||data?.profile?.name||'Alex'}</span></button></div></header>
 {errorBox}
 <main className={['Discover','Saved things'].includes(page)?'feed-page':'page-scroll'} key={page}>
 {['Discover','Saved things'].includes(page)?<><div className="feed-heading"><h1 className="page-title">{page==='Discover'?'For you':'Saved'}</h1></div>
 {page==='Discover'&&data?.fallback?.active&&<div className="field-help feed-fallback" role="status"><p>{data.fallback.message}</p>{data.fallback.recommendation&&<p className="gemini-recommendation"><strong>Gemini suggestion</strong><br/>{data.fallback.recommendation}</p>}</div>}
 {data?.recommendation_mode&&<p className="related-notice">Similar picks Â· some preferences relaxed</p>}
 <div className={listView?'opportunity-list':'opportunity-feed'} ref={feedRef} tabIndex={0} role="region" aria-label={listView?'Text-only opportunity list':'Opportunity feed. Swipe or scroll to explore.'} key={page+JSON.stringify([difficulty,kinds,interests,goals,preferences,data?.checkin?.effort,listView])}>
 {visible.map(o=>{const q=quests.find(x=>x.id===o.suggested_quest_id);return <article className="quest-card" key={o.id}><button className="quest-card-open" aria-label={`View details: ${simpleTitle(o)}`} onClick={()=>{setError('');setDetail(o.id)}}>{!listView&&<div className="quest-card-photo"><Art opportunity={o} src={feedPhotos.get(o.id)}/></div>}<div className="quest-card-body"><h2 className="quest-card-title">{simpleTitle(o)}</h2><p className="quest-card-sub">{subline(o)}</p><div className="quest-chips">{o.recommendation_type==='neutral'&&<span>Suggestion</span>}<span>{kindLabel(o.kind)}</span>{o.minutes>0&&<span>{o.minutes} min first step</span>}{q?.points>0&&<span>+{q.points} âœ¦</span>}{o.general_task&&<span>OneThing task</span>}{o.sample&&<span>Sample</span>}</div>{!listView&&<p className="quest-card-desc">{blurb(o.description)}</p>}</div></button><button className={`save-float ${o.saved?'is-saved':''}`} aria-label={`${o.saved?'Unsave':'Save'} ${simpleTitle(o)}`} aria-pressed={o.saved} disabled={busy} onClick={()=>action(()=>toggleSave(o))}><Bookmark size={20} fill={o.saved?'currentColor':'none'}/></button></article>})}
 {!visible.length&&!feedLoading&&<div className="empty"><Sprout size={32}/><h2>{page==='Saved things'?'Nothing saved yet.':'No matches.'}</h2><p>{page==='Saved things'?'Tap the bookmark on any quest to keep it here.':'Try fewer filters.'}</p><button className="primary" onClick={()=>{resetFilters();navigate('Discover')}}>{page==='Saved things'?'Explore quests':'Clear filters'}<ArrowRight size={16}/></button></div>}
 {page==='Discover'&&<div ref={endOfFeedRef} className="feed-load-sentinel" aria-busy={feedLoading}>
 {feedLoading&&<p role="status" className="feed-loading"><span className="feed-loading-dot"/>Loadingâ€¦</p>}
 {feedError?<div className="feed-load-error" role="alert"><p>{feedError}</p><button className="secondary" disabled={feedLoading} onClick={()=>{fetchFeed(true).catch(()=>{})}}>Try loading more again</button></div>:data?.has_more&&!feedLoading?<button className="text-link" onClick={()=>{fetchFeed(true).catch(()=>{})}}>Load more opportunities<ArrowRight size={15}/></button>:!feedLoading&&visible.length>0?<p className="fictional-note">That's everything for now.</p>:null}
 </div>}</div></>:<><div className="page-heading"><h1 className="page-title">{page==='My progress'?'Progress':'Recap'}</h1></div>
 {page==='My recap'?<Recap data={analytics} onExplore={()=>{resetFilters();navigate('Discover')}}/>:<><div className="progress-summary"><button className="streak-chip" aria-label="View streak calendar" onClick={()=>setCalendarOpen(true)}><Flame size={16}/>{progress.streak||0} day streak</button><p>{progress.active_today?"Today's quest is done.":'Complete a quest today to keep your streak.'}</p><small>Best: {progress.longest_streak||0} days Â· Pacific time</small></div><Climb progress={progress} fromPoints={climbFrom}/><section className="progress-panel"><div className="stats"><div><strong>{progress.completed_count}</strong><span>quests completed</span></div><div><strong>{progress.saved_count}</strong><span>things saved</span></div></div><h2>Completed</h2>{progress.activity.length?progress.activity.map(a=><div className="activity" key={a.id||a.quest_id}><span className="tick"><Check size={17}/></span><div><strong>{a.title}</strong><small>{new Date(a.completed_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})} Â· Quest completed</small></div><b>+{a.points}</b></div>):<p className="field-help">Completed quests will show up here.</p>}</section><Analytics today={progress.today} clock={progress.demo_clock} onDateChange={async value=>{await api.demoDate(value);await load();}} data={analytics} onRecap={()=>navigate('My recap')}/></>}
 </>}
 </main>
 {['Discover','Saved things'].includes(page)&&<div className="feed-toolbar"><button className="view-toggle" aria-label={listView?'Switch to image feed':'Switch to text-only list'} aria-pressed={listView} onClick={()=>{const next=!listView;setListView(next);localStorage.setItem('one-thing-view',next?'list':'images')}}>{listView?<Image size={17}/>:<List size={17}/>}<span>{listView?'Images':'List'}</span></button>{page==='Discover'&&<button onClick={()=>setFiltersOpen(true)}><SlidersHorizontal size={17}/>Filters{filterCount>0&&<span className="filter-count">{filterCount}</span>}</button>}</div>}
 <nav className="bottom-nav" aria-label="Main navigation">{NAV.map(([value,label,Icon])=><button key={value} className={page===value?'active':''} aria-current={page===value?'page':undefined} onClick={()=>navigate(value)}><span className="nav-icon"><Icon size={21}/>{value==='Saved things'&&progress.saved_count>0&&<span className="nav-count">{progress.saved_count}</span>}</span><span>{label}</span></button>)}</nav></div>
 {profileOpen&&<Modal title="Your profile" onClose={()=>setProfileOpen(false)} className="filter-sheet profile-sheet"><ProfileEditor profile={data?.profile||{interests,goals,skills,preferences}} onSave={async draft=>{await api.profile(draft);setInterests(draft.interests);setGoals(draft.goals);setSkills(draft.skills);setPreferences(draft.preferences);relatedFeed.current=false;await load(false);setProfileRevision(n=>n+1);setProfileOpen(false);navigate('Discover')}}/></Modal>}
 {calendarOpen&&<Modal title="Your streak calendar" onClose={()=>setCalendarOpen(false)}><StreakCalendar progress={progress}/></Modal>}
 {filtersOpen&&<Modal title="Filters" onClose={()=>setFiltersOpen(false)} className="filter-sheet"><p>Quests match any of your choices within each group. Time, difficulty and location still apply.</p><div className="feed-filters"><label>Step size<select aria-label="Step size" value={difficulty} onChange={e=>setDifficulty(e.target.value)}>{['Any','Small','Medium','Big'].map(v=><option key={v}>{v}</option>)}</select></label></div><PreferenceFields interests={interests} setInterests={setInterests} goals={goals} setGoals={setGoals} preferences={preferences} setPreferences={setPreferences}/><ChoiceList label="Opportunity types Â· none selected means all" choices={data?.kinds||SOURCES} value={kinds} onChange={setKinds}/>{data?.data_mode==='catalog'&&<MetadataFilters value={metadata} onChange={setMetadata}/>}{errorBox}<div className="sheet-actions"><button className="text-link" onClick={resetFilters}>Reset filters</button><button className="primary" disabled={busy||!skills.length} onClick={()=>action(async()=>{await api.profile({goal:goals[0]||GOALS[0],goals,interests,skills,preferences});relatedFeed.current=false;await load();setFiltersOpen(false)})}>Apply filters<ArrowRight size={16}/></button></div></Modal>}
 {selected&&<Modal title="Details" onClose={()=>setDetail(null)} className="detail-sheet"><div className="detail-image"><Art opportunity={selected} src={feedPhotos.get(selected.id)}/></div><div className="quest-chips detail-chips"><span>{kindLabel(selected.kind)}</span>{selectedQuest?.minutes>0&&<span>{selectedQuest.minutes} min first step</span>}{selectedQuest?.points>0&&<span>+{selectedQuest.points} âœ¦</span>}<span>{selected.sample?'Sample':'From the catalog'}</span></div><h2>{simpleTitle(selected)}</h2><p className="provider">{subline(selected)}</p>{selected.recommendation_type==='neutral'&&<p className="field-help">A general wellbeing alternative, offered because no available opportunity matches your interests and goals with these filters.</p>}<p className="detail-desc">{blurb(selected.description,320)}</p>{selectedQuest&&<div className="quest-preview"><span className="eyebrow">Your first step</span><h3>{selectedQuest.title}</h3><p>{selectedQuest.description}</p></div>}{errorBox}<div className="sheet-actions"><button className="secondary" disabled={busy} aria-pressed={selected.saved} onClick={()=>action(()=>toggleSave(selected))}><Bookmark size={17} fill={selected.saved?'currentColor':'none'}/>{selected.saved?'Saved':'Save'}</button><button className="primary" disabled={busy||!selectedQuest} onClick={()=>action(startQuest)}>{selectedQuest?.completed?'View quest':'Start quest'}<ArrowRight size={16}/></button></div><details className="more-details"><summary>More details</summary><div className="opportunity-facts"><p><strong>Full title</strong>{selected.title}</p>{selected.description&&blurb(selected.description,320)!==selected.description&&<p><strong>Full description</strong>{selected.description}</p>}{selected.location&&<p><strong>Where</strong>{selected.location}</p>}{selected.commitment&&<p><strong>Commitment</strong>{selected.commitment}</p>}{selected.personalization&&<><p><strong>Challenge (estimated)</strong>{selected.personalization.challenge_levels.join(', ')}</p><p><strong>Duration</strong>{durationLabel(selected.personalization.duration)}</p></>}{selected.personalization?.assessment&&<><p><strong>Experience (estimated)</strong>{selected.personalization.assessment.experience_level}</p><p><strong>Cost</strong>{selected.personalization.assessment.cost}</p><p><strong>Prerequisites</strong>{selected.personalization.assessment.prerequisite_status}</p><p><strong>Schedule</strong>{selected.personalization.assessment.schedule_type}</p></>}{selected.requirements?.length>0&&<div><strong>Requirements</strong><ul>{selected.requirements.map(r=><li key={r}>{r}</li>)}</ul></div>}{!selected.sample&&!selected.general_task&&selected.source_url&&<p><a href={selected.source_url} target="_blank" rel="noopener noreferrer">View the original listing</a></p>}<p className="fictional-note">{selected.general_task?'Self-guided OneThing task from the supplied list. Difficulty follows the list; time is an estimate of active effort. Adapt the task to your circumstances.':selected.sample?'A fictional opportunity for practice.':<>Collected {new Date(selected.collected_at).toLocaleDateString()}. Verify current details at the source.</>}</p></div></details></Modal>}
 {active&&<Modal title="Your first step" onClose={()=>setActive(null)} className="quest-sheet"><h2>{active.title}</h2><div className="quest-meta"><span>{active.size||'Medium'} step</span><span>{active.minutes} min (estimated)</span><span>+{active.points} points</span>{active.daily&&<span>Daily practice</span>}</div><p>{active.description}</p><div className="checklist">{active.steps.map((step,i)=><label key={step}><input type="checkbox" checked={checked.includes(i)} onChange={()=>setChecked(checked.includes(i)?checked.filter(x=>x!==i):[...checked,i])}/><span>{step}</span></label>)}</div>{errorBox}<button className="primary wide" disabled={busy||active.completed||checked.length!==active.steps.length} onClick={()=>action(async()=>{const before=progress.points;const result=await api.complete(active.id);setClimbFrom(result.points_earned>0?before:null);await load(false);setActive(null);setReward(result.points_earned)})}>{active.completed?'Already completed':busy?'Savingâ€¦':'Mark complete'}<Check size={18}/></button><p className="fictional-note">Do the steps in your own time. Completion is self-reported.</p></Modal>}
 {reward!==null&&<Modal title="Quest complete" onClose={()=>setReward(null)} className="celebration">{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)&&<div className="milestone-confetti" aria-hidden="true">{Array.from({length:12},(_,i)=><i key={i} style={{'--i':i}}/>)}</div>}<div className="reward-points">+{reward}<span>points</span></div><h2>{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)?<>Level {climbPosition(progress.points).level}.</>:<>Quest <em>complete.</em></>}</h2><Climb progress={progress} fromPoints={climbFrom}/><button className="primary wide" onClick={()=>{setReward(null);navigate('My progress')}}>See progress<ArrowRight size={18}/></button><button className="text-link" onClick={()=>setReward(null)}>Keep exploring</button></Modal>}
 </div>;
}
