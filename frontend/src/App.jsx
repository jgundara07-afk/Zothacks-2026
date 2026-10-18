import React, {useState, useEffect, useRef} from 'react';
import {ArrowRight, ArrowLeft, Bookmark, Check, Compass, Flag, Mountain, Sparkles, Sprout, Clock3, X, SlidersHorizontal, Pencil, Flame, ChevronDown, List, Image, Leaf, BookOpen, Users, Briefcase, Code2, UserRound} from 'lucide-react';
import {api} from './api';
import {authConfigured,supabase} from './auth';
import {logout} from './authFlow';
import {verificationRedirectError} from './authRedirect';
import ProfileEditor from './components/ProfileEditor';
import UserContextFields,{emptyContext} from './components/UserContextFields';
import contextOptions from '../../shared/user_context.json';
import MetadataFilters,{emptyMetadataFilters,metadataQuery} from './components/MetadataFilters';
import {durationLabel} from './utils/duration';
import Print from './components/Print';
import {photoFor,photosForList} from './utils/photos';
import {simpleTitle,subline,kindLabel,blurb} from './utils/titles';
import {CATEGORIES,categoryFor} from './utils/categories';
import FilterBar from './components/FilterBar';
import {effortLabel,effortRank,stepBreakdown} from './utils/effort';
import Recap from './pages/RecapPage';
import Analytics from './components/Analytics';
import StreakCalendar from './components/StreakCalendar';
import Onboarding from './components/Onboarding';
import Climb from './components/Climb';
import Atlas from './components/Atlas';
import PointsTimeline from './components/PointsTimeline';
import AchievementGallery from './components/AchievementGallery';
import AchievementUnlock from './components/AchievementUnlock';
import RewardSeal from './components/RewardSeal';
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
// Five-pip effort meter: Lazy, Easy, Medium, Hard, Locked-in.
function Effort({d,compact}){const r=effortRank(d);return <span className={`effort-pill e${r}${compact?' compact':''}`} aria-label={`Effort: ${effortLabel(d)}`}><span className="pips" aria-hidden="true">{[1,2,3,4,5].map(i=><i key={i} className={i<=r?'on':''}/>)}</span>{effortLabel(d)}</span>}

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
 const [session,setSession]=useState(null),[ready,setReady]=useState(!authConfigured);
 const [verificationError]=useState(()=>verificationRedirectError(window.location.href));
 useEffect(()=>{if(verificationError)window.history.replaceState(null,'',window.location.pathname)},[verificationError]);
 useEffect(()=>{
  if(!supabase)return;
  let active=true;
  const {data:{subscription}}=supabase.auth.onAuthStateChange((_event,next)=>{if(active){setSession(next);setReady(true)}});
  supabase.auth.getSession().then(({data})=>{if(active){setSession(data.session);setReady(true)}}).catch(()=>{if(active)setReady(true)});
  return()=>{active=false;subscription.unsubscribe()};
 },[]);
 if(!ready)return <div className="phone-shell demo-auth"><main className="demo-auth-body" role="status">Restoring your session…</main></div>;
 if(!session)return <Onboarding data={{}} hasProfile={false} error={verificationError}/>;
 return <OneThingApp key={session.user.id} session={session} onLogout={async()=>{await logout();setSession(null)}}/>;
}

function OneThingApp({session,onLogout}){
 const [climbFrom,setClimbFrom]=useState(null);
 useEffect(()=>{const update=e=>setProgress(old=>({...old,achievements:e.detail}));window.addEventListener('onething-achievements',update);return()=>window.removeEventListener('onething-achievements',update)},[]);
 // Achievement celebrations: the first loaded list is the baseline; anything unlocked after that is queued once.
 // The logo returns to the title screen; the intro animation only plays on the first visit.
 const [returningHome,setReturningHome]=useState(false);
 const knownBadges=useRef(null),[unlockQueue,setUnlockQueue]=useState([]),[mapFocus,setMapFocus]=useState(null),[tabDir,setTabDir]=useState('forward');
 const [searchQuery,setSearchQuery]=useState('');
 const [context,setContext]=useState({...emptyContext});
 const [matchMode,setMatchMode]=useState('any'),[feedSort,setFeedSort]=useState('relevance'),[hideSaved,setHideSaved]=useState(false);
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
  const filters={...metadataQuery(metadata),q:searchQuery,match_mode:matchMode,sort:feedSort,hide_saved:String(hideSaved),interests,goals,challenges:preferences.challenges,time:preferences.time,locations:preferences.locations,commitment:preferences.commitment,step_size:difficulty,kind:kinds,limit:40};
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
   let f=await (relatedFeed.current?api.recommendations({...filters,offset:append?nextFeedOffset(feedData.current):0}):api.feed({...filters,offset:append?nextFeedOffset(feedData.current):0}));
   if(opening&&!append&&!f.opportunities.length&&!f.fallback?.recommendation){relatedFeed.current=true;f=await api.recommendations({...filters,offset:0});}
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
  if(!initialized.current){if(f.profile){setContext({...emptyContext,...f.profile.context});setGoal(f.profile.goal);setInterests(f.profile.interests.filter(t=>options.interests.includes(t)).slice(0,options.max_selected_interests));setGoals((f.profile.goals||[]).slice(0,3));setPreferences({...emptyPreferences,...f.profile.preferences});setSkills(f.profile.skills);setOpening(false)}if(f.checkin){setMood(f.checkin.mood);setEffort(f.checkin.effort)}initialized.current=true}
 }
 useEffect(()=>{load().catch(e=>setError(e.message))},[]);
 useEffect(()=>{if(opening||filtersOpen)return;++feedVersion.current;feedRequest.current=null;setFeedLoading(true);setFeedError('');const timer=setTimeout(()=>{setError('');fetchFeed().catch(e=>setError(e.message))},150);return()=>clearTimeout(timer)},[opening,filtersOpen,profileRevision,JSON.stringify([interests,goals,preferences,difficulty,kinds,metadata,searchQuery,matchMode,feedSort,hideSaved])]);
 async function action(fn){setBusy(true);setError('');try{await fn()}catch(e){setError(e.message)}finally{setBusy(false)}}
 function resetFilters(){setSearchQuery('');setMatchMode('any');setFeedSort('relevance');setHideSaved(false);relatedFeed.current=false;setMetadata({...emptyMetadataFilters});setInterests([]);setGoals([]);setPreferences({...emptyPreferences});setDifficulty('Any');setKinds([]);setMode('Anywhere');setGoalFilter('Any goal');setSkillFilter('Any skill');setInterestFilter('Any interest')}
 function navigate(next){const index=tab=>NAV.findIndex(([value])=>value===tab);if(next!==page)setTabDir(index(next)<index(page)?'back':'forward');if(next!=='My progress')setMapFocus(null);setPage(next);setError('')}
 useEffect(()=>{
  const unlocked=(progress.achievements||[]).filter(b=>b.unlocked);if(!progress.achievements?.length)return;
  if(knownBadges.current===null){knownBadges.current=new Set(unlocked.map(b=>b.id));return}
  const fresh=unlocked.filter(b=>!knownBadges.current.has(b.id));if(!fresh.length)return;
  fresh.forEach(b=>knownBadges.current.add(b.id));setUnlockQueue(queue=>[...queue,...fresh]);
 },[progress.achievements]);
 function saveContext(){return {active:!!(interests.length||goals.length||kinds.length||preferences.time.length||preferences.locations.length||Object.values(metadata).some(value=>Array.isArray(value)?value.length:!!value)),challenges:preferences.challenges}}
 function openFilters(){setContext({...emptyContext,...data?.profile?.context});setFiltersOpen(true)}
 async function toggleSave(o){if(o.saved)await api.unsave(o.id);else await api.save(o.id,saveContext());await load(hideSaved);if(detail===o.id&&(page==='Saved things'?o.saved:hideSaved&&!o.saved))setDetail(null)}
 const all=(page==='Saved things'?savedRows:(data?.opportunities||[])).map(o=>{
  const variant=chooseVariant(o,quests,{availableMinutes:contextOptions.first_step_minutes[data?.profile?.context?.availability],stepSize:difficulty,preferences,defaultEffort:data?.checkin?.effort});
  return variant?{...o,minutes:variant.minutes,suggested_quest_id:variant.id,difficulty:o.personalization&&!o.sample?o.difficulty:variant.difficulty,preparation_difficulty:variant.difficulty,effort:variant.effort,size:variant.size,hasVariant:true}:{...o,hasVariant:false};
 });
 const visible=all.filter(o=>page==='Saved things'?o.saved:o.hasVariant&&(data?.data_mode==='catalog'||matchesOpportunity(o,{interests,goals,preferences})&&(!kinds.length||kinds.includes(o.kind))));
 const feedPhotos=photosForList(visible);
 // The card you land on gets .in-view (photo settles, text rises; styles/smooth.css).
 useEffect(()=>{const root=feedRef.current;if(!root||listView)return;const io=new IntersectionObserver(es=>es.forEach(e=>e.target.classList.toggle('in-view',e.isIntersecting)),{root,threshold:.6});root.querySelectorAll('.quest-card').forEach(c=>io.observe(c));root.classList.add('watching');return()=>{io.disconnect();root.classList.remove('watching')}},[data,page,listView]);
 const selected=detail?all.find(o=>o.id===detail):null;
 const selectedSteps=selected?quests.filter(q=>q.opportunity_id===selected.id&&q.project).sort((a,b)=>a.project.step-b.project.step):[];
 // A project opens on its next unfinished step; other opportunities on their suggested quest.
 const selectedQuest=selected&&(selectedSteps.find(q=>!q.completed)||quests.find(q=>q.id===selected.suggested_quest_id)||quests.find(q=>q.opportunity_id===selected.id));
 const activeChips=[
  ...interests.map(v=>({label:v,remove:()=>setInterests(interests.filter(x=>x!==v))})),
  ...goals.map(v=>({label:v,remove:()=>setGoals(goals.filter(x=>x!==v))})),
  ...['challenges','time','locations'].flatMap(key=>preferences[key].map(v=>({label:v,remove:()=>setPreferences({...preferences,[key]:preferences[key].filter(x=>x!==v)})}))),
  ...kinds.map(v=>({label:v,remove:()=>setKinds(kinds.filter(x=>x!==v))})),
  ...Object.entries(metadataQuery(metadata)).map(([key,v])=>({label:`${key}: ${v}`,remove:()=>setMetadata({...metadata,[key]:key==='max_minutes'?'':'Any'})})),
  ...(searchQuery?[{label:`Search: ${searchQuery}`,remove:()=>setSearchQuery('')}]:[]),
  ...(difficulty!=='Any'?[{label:`${difficulty} step`,remove:()=>setDifficulty('Any')}]:[]),
  ...(preferences.commitment!=='A mix of both'?[{label:preferences.commitment,remove:()=>setPreferences({...preferences,commitment:'A mix of both'})}]:[]),
  ...(matchMode==='all'?[{label:'Match every choice',remove:()=>setMatchMode('any')}]:[]),
  ...(hideSaved?[{label:'Hide saved',remove:()=>setHideSaved(false)}]:[]),
  
 ];
 const filterCount=Number(!!searchQuery.trim())+Number(matchMode==='all')+Number(hideSaved)+(difficulty!=='Any')+interests.length+goals.length+preferences.challenges.length+preferences.time.length+preferences.locations.length+(preferences.commitment!=='A mix of both')+kinds.length+Object.keys(metadataQuery(metadata)).length;
 const unlocking=reward===null&&!active?unlockQueue[0]:null;
 const modalOpen=!!(profileOpen||selected||active||reward!==null||filtersOpen||calendarOpen||unlocking);
 const loadMoreRef=useRef(null);loadMoreRef.current=()=>fetchFeed(true);
 useEffect(()=>{
  const root=feedRef.current,target=endOfFeedRef.current;
  if(opening||page!=='Discover'||modalOpen||feedLoading||feedError||!data?.has_more||!root||!target||!('IntersectionObserver' in window))return;
  const observer=new IntersectionObserver(entries=>{
   if(entries.some(entry=>entry.isIntersecting)&&feedRequest.current===null)loadMoreRef.current().catch(()=>{});
  },{root,rootMargin:'0px 0px 240px 0px',threshold:0});
  observer.observe(target);return()=>observer.disconnect();
 },[opening,page,modalOpen,feedLoading,feedError,data?.has_more,data?.opportunities.length,listView]);
 // After a completion the feed moves a project on to its next step, or drops a finished opportunity (it never returns).
 function advanceFeed(quest){
  const next=quests.filter(q=>q.opportunity_id===quest.opportunity_id&&q.project&&q.id!==quest.id&&!q.completed).sort((a,b)=>a.project.step-b.project.step)[0];
  setQuests(old=>old.map(q=>q.id===quest.id?{...q,completed:true}:q));
  setData(old=>{if(!old)return old;const updated=next?{...old,opportunities:old.opportunities.map(o=>o.id===quest.opportunity_id?{...o,suggested_quest_id:next.id,minutes:next.minutes}:o)}:{...old,opportunities:old.opportunities.filter(o=>o.id!==quest.opportunity_id),page_count:Math.max(0,(old.page_count??old.opportunities.length)-1)};feedData.current=updated;return updated});
 }
 async function startQuest(){if(!selected.saved){await api.save(selected.id,saveContext());await load(false)}setDetail(null);setActive({...selectedQuest,source_kind:selected.kind});setChecked([])}
 function nextCard(e){const card=e.currentTarget.closest('article'),sibling=card.nextElementSibling,next=sibling?.tagName==='ARTICLE'||data?.has_more?sibling:card.parentElement.firstElementChild;card.parentElement.scrollTo({top:next.offsetTop-card.parentElement.firstElementChild.offsetTop,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}
 const errorBox=error&&<div role="alert" className="error"><span>{error}</span><button type="button" disabled={busy} onClick={()=>action(load)}>Retry</button></div>;

 const topPick=visible[0];
 const topQuest=topPick&&(quests.find(q=>q.id===topPick.suggested_quest_id)||quests.find(q=>q.opportunity_id===topPick.id));
 const sample=(data?.opportunities||[]).find(o=>o.id==='sample-networking-backend')||all[0];
 async function saveOnboarding(){relatedFeed.current=false;let ok=false;await action(async()=>{await api.profile({context,goal:goals[0]||GOALS[0],goals,interests,skills,preferences});await load();ok=true});return ok}
 // If even neutral alternatives cannot fit the current constraints, explicitly keep the first
 // interest, drop goals and places, then open the feed.
 async function widenOnboarding(){const prefs={...preferences,locations:[]},keep=interests.slice(0,1);await action(async()=>{await api.profile({goal:GOALS[0],goals:[],interests:keep,skills,preferences:prefs});setGoals([]);setInterests(keep);setPreferences(prefs);enterApp()})}
 function enterApp(){setOpening(false);setKinds([]);setPage('Discover')}
 if(opening&&error&&!data)return <div className="phone-shell demo-auth"><header className="welcome-header"><span className="brand">OneThing</span></header><main className="demo-auth-body"><h1>Let's try <em>again.</em></h1><p className="error" role="alert">{error}</p><button className="primary wide" disabled={busy} onClick={()=>action(load)}>Retry<ArrowRight size={18}/></button><button className="secondary wide" disabled={busy} onClick={()=>action(onLogout)}>Log out</button></main></div>;
 if(opening)return <Onboarding authenticated initialStep={returningHome?0:1} skipIntro={returningHome} context={context} setContext={setContext} data={data} busy={busy} error={error} hasProfile={!!data?.profile} interests={interests} setInterests={setInterests} goals={goals} setGoals={setGoals} skills={skills} setSkills={setSkills} preferences={preferences} setPreferences={setPreferences} stepSize={difficulty} setStepSize={setDifficulty} sample={sample} topPick={topPick} topQuest={topQuest} onSave={saveOnboarding} onEnter={enterApp} onWiden={widenOnboarding} onSkip={()=>action(async()=>{if(!data.profile){await api.profile({goal:GOALS[0],interests:['Design','Community'],skills:['Writing']});await load()}resetFilters();enterApp()})}/>;

 return <div className="phone-shell"><div className="app-surface" inert={modalOpen?true:undefined}><header className="app-header"><a className="brand" href="#" aria-label="OneThing home" onClick={e=>{e.preventDefault();setError('');setReturningHome(true);setOpening(true)}}>OneThing</a><div className="header-actions">{['Discover','Saved things'].includes(page)&&<button className="header-icon" aria-label={listView?'Switch to image feed':'Switch to text-only list'} aria-pressed={listView} onClick={()=>{const next=!listView;setListView(next);localStorage.setItem('one-thing-view',next?'list':'images')}}>{listView?<Image size={18}/>:<List size={18}/>}</button>}{progress.demo_clock?.simulated&&<button className="demo-date-badge" onClick={()=>navigate('My progress')}>Demo · {progress.today}</button>}<button className="streak-chip" aria-label={`View streak calendar, ${progress.streak||0} day streak`} onClick={()=>setCalendarOpen(true)}><Flame size={15}/>{progress.streak||0}</button><button className="profile-button" aria-label="Edit profile" onClick={()=>{setError('');setProfileOpen(true)}}><UserRound size={17}/><span>{data?.profile?.name||session.user.user_metadata?.name||session.user.email?.split('@')[0]||'You'}</span></button></div><div className="xp-strip" title={`${progress.points%100} of 100 XP to your next milestone`} aria-hidden="true" style={{'--xp':(progress.points%100)/100}}><i/></div></header>
 {errorBox}
 <main className={(['Discover','Saved things'].includes(page)?'feed-page':'page-scroll')+' tab-enter'} data-dir={tabDir} key={page}>
 {['Discover','Saved things'].includes(page)?<>{page==='Discover'&&<FilterBar feedRef={feedRef} count={filterCount} matches={data?.matched_count??data?.total??0} chips={activeChips.map(c=>({...c,remove:()=>{relatedFeed.current=false;c.remove()}}))} notes={data?.context_applied?(data.context_notes||[]):[]} onOpen={openFilters}/>}
 <div className={listView?'opportunity-list':'opportunity-feed'} ref={feedRef} tabIndex={0} role="region" aria-label={listView?'Text-only opportunity list':'Opportunity feed. Swipe or scroll to explore.'} key={page+JSON.stringify([difficulty,kinds,interests,goals,preferences,data?.checkin?.effort,listView])}>
 {visible.map(o=>{const q=quests.find(x=>x.id===o.suggested_quest_id);const cat=categoryFor(o);return <article className={`quest-card cat-${cat}`} key={o.id}><button className="quest-card-open" aria-label={`View details: ${simpleTitle(o)}`} onClick={()=>{setError('');setDetail(o.id)}}>{!listView&&<div className="quest-card-photo"><Art opportunity={o} src={feedPhotos.get(o.id)}/><span className="quest-category">{CATEGORIES[cat]}</span></div>}<div className="quest-card-body"><h2 className="quest-card-title">{simpleTitle(o)}</h2><p className="quest-card-sub">{subline(o)}</p><div className="quest-chips">{o.recommendation_type==='neutral'&&<span>Suggestion</span>}<span>{kindLabel(o.kind)}</span>{q?.project&&<span>Step {q.project.step} of {q.project.total}</span>}{o.minutes>0&&<span>{q?.action?`${q.action} · ${q.minutes??o.minutes} min`:`${o.minutes} min first step`}</span>}{q&&<Effort d={q.difficulty}/>}{q?.points>0&&<span className="chip-xp">+{q.points} XP</span>}{o.general_task&&<span>OneThing task</span>}{o.sample&&<span>Sample</span>}</div>{!listView&&<p className="quest-card-desc">{blurb(o.description)}</p>}</div></button><button className={`save-float ${o.saved?'is-saved':''}`} aria-label={`${o.saved?'Unsave':'Save'} ${simpleTitle(o)}`} aria-pressed={o.saved} disabled={busy} onClick={()=>action(()=>toggleSave(o))}><Bookmark size={20} fill={o.saved?'currentColor':'none'}/></button></article>})}
 {!visible.length&&!feedLoading&&<div className="empty"><Sprout size={32}/><h2>{page==='Saved things'?'Nothing saved yet.':'No matches.'}</h2><p>{page==='Saved things'?'Tap the bookmark on any quest to keep it here.':'Try fewer filters.'}</p><button className="primary" onClick={()=>{resetFilters();navigate('Discover')}}>{page==='Saved things'?'Explore quests':'Clear filters'}<ArrowRight size={16}/></button></div>}
 {page==='Discover'&&<div ref={endOfFeedRef} className="feed-load-sentinel" aria-busy={feedLoading}>
 {feedLoading&&<p role="status" className="feed-loading"><span className="feed-loading-dot"/>Loading…</p>}
 {feedError?<div className="feed-load-error" role="alert"><p>{feedError}</p><button className="secondary" disabled={feedLoading} onClick={()=>{fetchFeed(true).catch(()=>{})}}>Try loading more again</button></div>:data?.has_more&&!feedLoading?<button className="text-link" onClick={()=>{fetchFeed(true).catch(()=>{})}}>Load more opportunities<ArrowRight size={15}/></button>:!feedLoading&&visible.length>0?<p className="fictional-note">That's everything for now.</p>:null}
 </div>}</div></>:<><div className="page-heading"><h1 className="page-title">{page==='My progress'?'Progress':'Recap'}</h1></div>
 {page==='My recap'?<Recap data={analytics} onExplore={()=>{resetFilters();navigate('Discover')}}/>:<><div className="progress-summary"><button className="streak-chip" aria-label="View streak calendar" onClick={()=>setCalendarOpen(true)}><Flame size={16}/>{progress.streak||0} day streak</button><p>{progress.active_today?"Today's quest is done.":'Complete a quest today to keep your streak.'}</p><small>Best: {progress.longest_streak||0} days · Pacific time</small></div><PointsTimeline activity={progress.activity} today={progress.today}/><Atlas progress={progress} focus={mapFocus}/><details className="badge-journal"><summary>Open your badge journal</summary><AchievementGallery badges={progress.achievements||[]}/></details><section className="progress-panel"><div className="stats"><div><strong>{progress.completed_count}</strong><span>quests completed</span></div><div><strong>{progress.saved_count}</strong><span>things saved</span></div></div><details className="completed-quests"><summary>Completed quests ({progress.completed_count})</summary>{progress.activity.length?progress.activity.map(a=><div className="activity" key={a.id||a.quest_id}><span className="tick"><Check size={17}/></span><div><strong>{a.title}</strong><small>{new Date(a.completed_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})} · Quest completed</small></div><b>+{a.points}</b></div>):<p className="field-help">Completed quests will show up here.</p>}</details></section><Analytics today={progress.today} clock={progress.demo_clock} onDateChange={async value=>{await api.demoDate(value);await load();}} data={analytics} onRecap={()=>navigate('My recap')}/></>}
 </>}
 </main>
 <nav className="bottom-nav" aria-label="Main navigation" style={{'--tab':Math.max(0,NAV.findIndex(([value])=>value===page))}}><span className="nav-marker" aria-hidden="true"/>{NAV.map(([value,label,Icon])=><button key={value} className={page===value?'active':''} aria-current={page===value?'page':undefined} onClick={()=>navigate(value)}><span className="nav-icon"><Icon size={21}/>{value==='Saved things'&&progress.saved_count>0&&<span className="nav-count">{progress.saved_count}</span>}</span><span>{label}</span></button>)}</nav></div>
 {profileOpen&&<Modal title="Your profile" onClose={()=>setProfileOpen(false)} className="filter-sheet profile-sheet"><button className="secondary auth-logout" type="button" disabled={busy} onClick={()=>action(onLogout)}>Log out</button><ProfileEditor profile={data?.profile||{context,interests,goals,skills,preferences}} onSave={async draft=>{await api.profile(draft);setContext({...emptyContext,...draft.context});setInterests(draft.interests);setGoals(draft.goals);setSkills(draft.skills);setPreferences(draft.preferences);relatedFeed.current=false;await load(false);setProfileRevision(n=>n+1);setProfileOpen(false);navigate('Discover')}}/></Modal>}
 {calendarOpen&&<Modal title="Your streak calendar" onClose={()=>setCalendarOpen(false)}><StreakCalendar progress={progress}/></Modal>}
 {filtersOpen&&<Modal title="Filters" onClose={()=>setFiltersOpen(false)} className="filter-sheet"><p>{matchMode==='all'?'Every selected interest and goal must match.':'Any choice in each interest or goal group can match.'} Different groups narrow results together. Location choices are alternatives; time and difficulty still apply.</p><details className="situation-filters"><summary>Your situation and constraints</summary><p className="field-help">These saved details also affect the feed. Edit them here, then Apply filters to save. City, school and situation influence ranking; supported availability and budget limits filter results.</p><UserContextFields value={context} onChange={setContext}/><button type="button" className="text-link" onClick={()=>setContext({...emptyContext})}>Clear situation filters</button></details><div className="feed-filters"><label>Match interests and goals<select value={matchMode} onChange={e=>setMatchMode(e.target.value)}><option value="any">Any choice in each group</option><option value="all">Every choice in each group</option></select></label><label>Sort opportunities<select value={feedSort} onChange={e=>setFeedSort(e.target.value)}><option value="relevance">Best match</option><option value="shortest">Shortest first step</option><option value="points">Most first-step points</option></select></label></div><div className="filter-visibility"><label><input type="checkbox" checked={hideSaved} onChange={e=>setHideSaved(e.target.checked)}/> Hide saved opportunities</label></div><label className="filter-search">Search opportunities<input type="search" value={searchQuery} onChange={e=>setSearchQuery(e.target.value)} maxLength={300} placeholder="Try frontend, research, or a provider"/></label><div className="feed-filters"><label>Step size<select aria-label="Step size" value={difficulty} onChange={e=>setDifficulty(e.target.value)}>{['Any','Small','Medium','Big'].map(v=><option key={v}>{v}</option>)}</select></label></div><PreferenceFields matchMode={matchMode} interests={interests} setInterests={setInterests} goals={goals} setGoals={setGoals} preferences={preferences} setPreferences={setPreferences}/><ChoiceList label="Opportunity types · none selected means all" choices={data?.kinds||SOURCES} value={kinds} onChange={setKinds}/>{data?.data_mode==='catalog'&&<MetadataFilters value={metadata} onChange={setMetadata}/>}{errorBox}<div className="sheet-actions"><button className="text-link" onClick={resetFilters}>Reset filters</button><button className="primary" disabled={busy||!skills.length} onClick={()=>action(async()=>{await api.profile({context,goal:goals[0]||GOALS[0],goals,interests,skills,preferences});relatedFeed.current=false;await load();setFiltersOpen(false)})}>Apply filters<ArrowRight size={16}/></button></div></Modal>}
 {selected&&<Modal title="Details" onClose={()=>setDetail(null)} className="detail-sheet"><div className="detail-image"><Art opportunity={selected} src={feedPhotos.get(selected.id)}/></div><div className="quest-chips detail-chips"><span>{kindLabel(selected.kind)}</span>{selectedQuest?.minutes>0&&<span>{selectedQuest.action?`${selectedQuest.action} · ${selectedQuest.minutes} min`:`${selectedQuest.minutes} min first step`}</span>}{selectedQuest&&<Effort d={selectedQuest.difficulty}/>}{selectedQuest?.points>0&&<span className="chip-xp">+{selectedQuest.points} XP</span>}<span>{selected.sample?'Sample':'From the catalog'}</span></div><h2>{simpleTitle(selected)}</h2><p className="provider">{subline(selected)}</p>{selected.match_details&&selected.recommendation_type!=='neutral'&&<p className="field-help">{[selected.match_details.title_terms?.length?`Title matches: ${selected.match_details.title_terms.join(', ')}.`:'',selected.matching_tags?.length?`Matching tags: ${selected.matching_tags.join(', ')}.`:''].filter(Boolean).join(' ')||'An available opportunity to explore.'}</p>}{selected.recommendation_type==='neutral'&&<p className="field-help">A general wellbeing alternative, offered because no available opportunity matches your interests and goals with these filters.</p>}<p className="detail-desc">{blurb(selected.description,320)}</p>{selectedQuest&&(selectedSteps.length>1?<div className="quest-preview project-roadmap"><span className="eyebrow">Your plan · {selectedSteps.filter(q=>q.completed).length} of {selectedSteps.length} steps done</span><ol>{selectedSteps.map(q=><li key={q.id} className={q.completed?"is-done":q.id===selectedQuest.id?"is-next":""}>{q.completed?<Check size={15}/>:<span className="step-number">{q.project.step}</span>}<span><strong>{q.action||q.title}</strong><small>{q.steps[0]}</small><span className="roadmap-meta"><Effort d={q.difficulty}/><em>{q.minutes} min</em><em className="xp">+{q.points} XP</em></span></span></li>)}</ol></div>:<div className="quest-preview"><span className="eyebrow">Your first step</span><h3>{selectedQuest.title}</h3><p>{selectedQuest.description}</p></div>)}{errorBox}<div className="sheet-actions"><button className="secondary" disabled={busy} aria-pressed={selected.saved} onClick={()=>action(()=>toggleSave(selected))}><Bookmark size={17} fill={selected.saved?'currentColor':'none'}/>{selected.saved?'Saved':'Save'}</button><button className="primary" disabled={busy||!selectedQuest} onClick={()=>action(startQuest)}>{selectedQuest?.completed?'View quest':'Start quest'}<ArrowRight size={16}/></button></div><details className="more-details"><summary>More details</summary><div className="opportunity-facts"><p><strong>Full title</strong>{selected.title}</p>{selected.description&&blurb(selected.description,320)!==selected.description&&<p><strong>Full description</strong>{selected.description}</p>}{selected.location&&<p><strong>Where</strong>{selected.location}</p>}{selected.commitment&&<p><strong>Commitment</strong>{selected.commitment}</p>}{selected.personalization&&<><p><strong>Challenge (estimated)</strong>{selected.personalization.challenge_levels.join(', ')}</p><p><strong>Duration</strong>{durationLabel(selected.personalization.duration)}</p></>}{selected.personalization?.assessment&&<><p><strong>Experience (estimated)</strong>{selected.personalization.assessment.experience_level}</p><p><strong>Cost</strong>{selected.personalization.assessment.cost}</p><p><strong>Prerequisites</strong>{selected.personalization.assessment.prerequisite_status}</p><p><strong>Schedule</strong>{selected.personalization.assessment.schedule_type}</p></>}{selected.requirements?.length>0&&<div><strong>Requirements</strong><ul>{selected.requirements.map(r=><li key={r}>{r}</li>)}</ul></div>}{!selected.sample&&!selected.general_task&&selected.source_url&&<p><a href={selected.source_url} target="_blank" rel="noopener noreferrer">View the original listing</a></p>}<p className="fictional-note">{selected.general_task?'Self-guided OneThing task from the supplied list. Difficulty follows the list; time is an estimate of active effort. Adapt the task to your circumstances.':selected.sample?'A fictional opportunity for practice.':<>Collected {new Date(selected.collected_at).toLocaleDateString()}. Verify current details at the source.</>}</p></div></details></Modal>}
 {active&&<Modal title="Your next step" onClose={()=>setActive(null)} className="quest-sheet"><h2>{active.title}</h2><div className="quest-meta"><Effort d={active.difficulty}/><span>{active.minutes} min (estimated)</span><span className="chip-xp">+{active.points} XP</span>{active.project?<span>Step {active.project.step} of {active.project.total}</span>:active.daily&&<span>Daily practice</span>}</div><p>{active.description}</p><div className="checklist">{stepBreakdown(active).map((step,i)=><label key={step.text}><input type="checkbox" checked={checked.includes(i)} onChange={()=>setChecked(checked.includes(i)?checked.filter(x=>x!==i):[...checked,i])}/><span>{step.text}</span>{active.steps.length>1&&<span className="step-meta"><Effort d={step.effort} compact/><em className="xp">+{step.xp} XP</em></span>}</label>)}</div>{errorBox}<button className="primary wide" disabled={busy||active.completed||checked.length!==active.steps.length} onClick={()=>action(async()=>{const before=progress.points;const result=await api.complete(active.id);setClimbFrom(result.points_earned>0?before:null);advanceFeed(active);await load(false);setActive(null);setReward(result.points_earned)})}>{active.completed?'Already completed':busy?'Saving…':'Mark complete'}<Check size={18}/></button><p className="fictional-note">Do the steps in your own time. Completion is self-reported.</p></Modal>}
 {reward!==null&&<Modal title="Quest complete" onClose={()=>setReward(null)} className="celebration">{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)&&<div className="milestone-confetti" aria-hidden="true">{Array.from({length:12},(_,i)=><i key={i} style={{'--i':i}}/>)}</div>}<RewardSeal points={reward}/><h2 className="reward-title">{climbFrom!==null&&crossedMilestone(climbFrom,progress.points)?<>Level {climbPosition(progress.points).level}.</>:<>Quest <em>complete.</em></>}</h2><Climb progress={progress} fromPoints={climbFrom}/>{unlockQueue.length>0&&<p className="reward-teaser"><Sparkles size={16}/>{unlockQueue.length===1?'A new achievement awaits.':`${unlockQueue.length} new achievements await.`}</p>}<button className="primary wide" onClick={()=>{setReward(null);navigate('My progress')}}>{unlockQueue.length?'Reveal achievement':'See progress'}<ArrowRight size={18}/></button><button className="text-link" onClick={()=>setReward(null)}>Keep exploring</button></Modal>}
 {unlocking&&<AchievementUnlock badge={unlocking} remaining={unlockQueue.length-1} onClose={()=>setUnlockQueue(queue=>queue.slice(1))} onView={()=>{setUnlockQueue(queue=>queue.slice(1));navigate('My progress');setMapFocus(unlocking.id)}}/>}
 </div>;
}
