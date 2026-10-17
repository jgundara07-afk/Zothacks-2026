import React from 'react';
import {ArrowUpRight,Bookmark,Clock3,Sparkles} from 'lucide-react';
import {OPPORTUNITY_ICONS,DEFAULT_ICON} from '../constants';

// One opportunity. inFeed = the big scroll-snapping Discover version (with artwork and a "next" button).
export default function OpportunityCard({o,index,total,inFeed,completed,busy,onToggleSave,onStart}){
 const Icon=OPPORTUNITY_ICONS[o.id]||DEFAULT_ICON;
 const startLabel=completed?'Done today':o.effort==='small'?'Take a small step':o.saved?'Start quest':'Give it a go';
 function scrollToNext(e){const card=e.currentTarget.closest('article');const next=card.nextElementSibling||card.parentElement.firstElementChild;card.parentElement.scrollTo({top:next.offsetTop-card.parentElement.firstElementChild.offsetTop,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}
 return <article className={'card '+o.color}>
  <div className="card-top"><span className="card-icon"><Icon size={23}/></span><span className="sample">SAMPLE OPPORTUNITY</span><button className={'bookmark '+(o.saved?'is-saved':'')} aria-label={o.saved?`Unsave ${o.title}`:`Save ${o.title}`} aria-pressed={o.saved} disabled={busy} onClick={()=>onToggleSave(o)}><Bookmark size={20} fill={o.saved?'currentColor':'none'}/></button></div>
  <div className="card-kind">{o.kind} <span>· {o.mode} · {o.organization}</span></div>
  {inFeed&&<div className="feed-art" aria-hidden="true"><Icon size={78} strokeWidth={1}/><span>{String(index+1).padStart(2,'0')} / {String(total).padStart(2,'0')}</span></div>}
  <h3>{o.title}</h3>
  <p>{o.description}</p>
  <div className="tags">{o.difficulty&&<span className="difficulty-tag">{o.difficulty} quest</span>}{o.tags.map(t=><span key={t}>{t}</span>)}</div>
  <div className="match"><Sparkles size={13}/>{o.matching_tags.length?`Because you picked ${o.matching_tags.slice(0,2).join(' + ')}`:'A new direction to explore'}</div>
  <div className="card-footer"><span><Clock3 size={14}/>{o.minutes} min first step</span><button disabled={busy} onClick={()=>onStart(o)}>{startLabel}<ArrowUpRight size={18}/></button></div>
  {inFeed&&<button className="feed-next" onClick={scrollToNext}>{index===total-1?'You explored this sample feed. Back to the start ↑':'Next possibility ↓'}</button>}
 </article>
}
