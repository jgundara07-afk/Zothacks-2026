import React from 'react';
import {ArrowRight,Bookmark,Sparkles} from 'lucide-react';
import {TOPIC_FILTERS} from '../constants';
import FeedFilters from '../components/FeedFilters';
import OpportunityCard from '../components/OpportunityCard';

// Used for both Discover (scrolling feed with filters) and Saved things (plain grid of saved cards).
export default function OpportunitiesPage({page,all,visible,quests,filters,effort,busy,onFilter,onReset,onToggleSave,onStart,onExplore}){
 const inFeed=page==='Discover';
 const isSaved=page==='Saved things';
 // Changing this key remounts the feed, which scrolls it back to the first card.
 const feedKey=page+filters.topic+filters.difficulty+filters.source+filters.mode+filters.goal+filters.skill+filters.gapSkills.join()+(effort||'');
 return <>
  <div className="section-heading"><h2>{inFeed?'A little inspiration for you':'Your saved possibilities'} <span>{visible.length}</span></h2><span className="curated"><Sparkles size={14}/> Thoughtfully matched</span></div>
  <div className="filters" aria-label="Filter opportunities">{TOPIC_FILTERS.map(f=><button key={f} className={filters.topic===f?'selected':''} onClick={()=>onFilter('topic',f)}>{f}</button>)}</div>
  {inFeed&&<FeedFilters all={all} filters={filters} onFilter={onFilter} onReset={onReset}/>}
  {inFeed&&<p className="feed-hint">Scroll or swipe for your next possibility ↓ · {visible.length} fictional opportunities</p>}
  <div className={inFeed?'cards opportunity-feed':'cards'} tabIndex={inFeed?0:undefined} role={inFeed?'region':undefined} aria-label={inFeed?'Opportunity feed. Scroll to explore.':undefined} key={feedKey}>
   {visible.map((o,index)=><OpportunityCard key={o.id} o={o} index={index} total={visible.length} inFeed={inFeed} completed={quests.find(q=>q.id===o.suggested_quest_id)?.completed} busy={busy} onToggleSave={onToggleSave} onStart={onStart}/>)}
  </div>
  {!visible.length&&<div className="empty"><Bookmark/><h3>{isSaved?'A space for your next possibility.':'Nothing here just yet.'}</h3><p>{isSaved?'Save something that catches your eye. Your next step will be waiting here.':'Try another difficulty, source, goal, or skill to find your next step.'}</p><button className="primary" onClick={onExplore}>Explore opportunities <ArrowRight size={16}/></button></div>}
  <div className="sample-disclaimer"><span>✳</span> A playground for possibilities. All opportunities are fictional samples for this demo.</div>
 </>
}
