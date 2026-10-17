import React,{useState,useEffect} from 'react';
import {api} from './api';
import {DEFAULT_FILTERS} from './constants';
import {useDialogFocus} from './hooks/useDialogFocus';
import {withDifficultyVariants,filterOpportunities,toggleItem} from './utils/opportunities';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import PageIntro from './components/layout/PageIntro';
import RightColumn from './components/layout/RightColumn';
import DailyCheckin from './components/DailyCheckin';
import OnboardingModal from './components/modals/OnboardingModal';
import QuestModal from './components/modals/QuestModal';
import RewardModal from './components/modals/RewardModal';
import OpportunitiesPage from './pages/OpportunitiesPage';
import ProgressPage from './pages/ProgressPage';
import ResumeLabPage from './pages/ResumeLabPage';
import RecapPage from './pages/RecapPage';

// Holds all shared state and talks to the API; the pages and components just display it.
export default function App(){
 const [page,setPage]=useState('Discover'),[data,setData]=useState(null),[quests,setQuests]=useState([]),[progress,setProgress]=useState({points:0,completed_count:0,saved_count:0,activity:[]}),[analytics,setAnalytics]=useState(null);
 const [error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [onboard,setOnboard]=useState(false),[active,setActive]=useState(null),[checked,setChecked]=useState([]),[reward,setReward]=useState(null);
 const [goal,setGoal]=useState('Explore my interests'),[interests,setInterests]=useState(['Design','Community']),[skills,setSkills]=useState(['Writing']);
 const [filters,setFilters]=useState(DEFAULT_FILTERS);
 const [mood,setMood]=useState('Okay'),[effort,setEffort]=useState('small'),[editingCheckin,setEditingCheckin]=useState(false);

 async function load(){try{const [f,q,p,a]=await Promise.all([api.feed(),api.quests(),api.progress(),api.analytics()]);setAnalytics(a);setData(f);if(f.checkin){setMood(f.checkin.mood);setEffort(f.checkin.effort)}setQuests(q.quests);setProgress(p);setError('');if(!f.profile)setOnboard(true);}catch(e){setError(e.message);}}
 useEffect(()=>{load()},[]);
 useDialogFocus(onboard||!!active||reward!==null,()=>{if(onboard&&data?.profile)setOnboard(false);else if(active)setActive(null);else if(reward!==null)setReward(null);},[onboard,active,reward]);

 // Runs an API call with the busy flag on and any error shown to the user.
 async function action(fn){setBusy(true);setError('');try{await fn();}catch(e){setError(e.message);}finally{setBusy(false)}}
 function editProfile(){if(data?.profile){setGoal(data.profile.goal);setInterests(data.profile.interests);setSkills(data.profile.skills)}setOnboard(true)}
 async function save(o){await api.save(o.id);await load()}
 function openQuest(o){setActive(quests.find(q=>q.id===o.suggested_quest_id)||quests.find(q=>q.opportunity_id===o.id));setChecked([])}
 const toggleSave=o=>action(async()=>{if(o.saved){await api.unsave(o.id);await load()}else{await save(o)}});
 const startQuest=o=>action(async()=>{if(!o.saved)await save(o);openQuest(o)});
 const saveProfile=()=>action(async()=>{await api.profile({goal,interests,skills});setOnboard(false);await load()});
 const saveCheckin=()=>action(async()=>{await api.checkin({mood,effort});setEditingCheckin(false);await load()});
 const completeQuest=()=>action(async()=>{const result=await api.complete(active.id);await load();setActive(null);setReward(result.points_earned)});

 const updateFilter=(key,value)=>setFilters({...filters,[key]:value});
 const resetFilters=()=>setFilters(DEFAULT_FILTERS);
 const exploreGaps=gapSkills=>{setFilters({...DEFAULT_FILTERS,gapSkills});setPage('Discover')};
 const goTo=name=>{setPage(name);resetFilters()};

 const all=withDifficultyVariants(data?.opportunities||[],quests,page,filters.difficulty);
 const visible=filterOpportunities(all,page,filters);

 return <div className="app">
 <Sidebar page={page} savedCount={progress.saved_count} onHome={()=>setPage('Discover')} onNavigate={goTo} onEditProfile={editProfile}/>
 <main className={page==='Discover'?'discover-page':''}><Header/>
 {error&&<div role="alert" className="error">{error}<button onClick={load}>Try again</button></div>}
 {!data&&!error?<div className="loading">Finding your next little step…</div>:<>
 <PageIntro page={page}/>
 {page==='Discover'&&<DailyCheckin checkin={data?.checkin} hasProfile={!!data?.profile} streak={progress.streak} mood={mood} effort={effort} editing={editingCheckin} busy={busy} onMood={setMood} onEffort={setEffort} onEdit={()=>setEditingCheckin(true)} onSubmit={saveCheckin}/>}
 <div className="content-grid"><div className="main-column">
 {page==='Resume lab'?<ResumeLabPage onExplore={exploreGaps}/>
 :page==='My recap'?<RecapPage data={analytics} onExplore={()=>goTo('Discover')}/>
 :page==='My progress'?<ProgressPage progress={progress} analytics={analytics} onDiscover={()=>setPage('Discover')} onRecap={()=>setPage('My recap')}/>
 :<OpportunitiesPage page={page} all={all} visible={visible} quests={quests} filters={filters} effort={data?.checkin?.effort} busy={busy} onFilter={updateFilter} onReset={resetFilters} onToggleSave={toggleSave} onStart={startQuest} onExplore={()=>goTo('Discover')}/>}
 </div><RightColumn progress={progress} interests={data?.profile?.interests||interests} onSeeProgress={()=>setPage('My progress')} onEditProfile={editProfile}/></div>
 <Footer/></>}
 </main>
 {onboard&&<OnboardingModal canClose={!!data?.profile} goal={goal} interests={interests} skills={skills} error={error} busy={busy} onGoal={setGoal} onToggleInterest={t=>setInterests(toggleItem(interests,t))} onToggleSkill={t=>setSkills(toggleItem(skills,t))} onClose={()=>setOnboard(false)} onSubmit={saveProfile}/>}
 {active&&<QuestModal quest={active} checked={checked} error={error} busy={busy} onToggleStep={i=>setChecked(toggleItem(checked,i))} onClose={()=>setActive(null)} onComplete={completeQuest}/>}
 {reward!==null&&<RewardModal points={reward} onSeeClimb={()=>{setReward(null);setPage('My progress')}} onClose={()=>setReward(null)}/>}
 </div>
}
