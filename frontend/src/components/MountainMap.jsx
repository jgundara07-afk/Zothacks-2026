import React,{useEffect,useRef,useState} from 'react';
import {Check,Flag,LockKeyhole,ChevronLeft,ChevronRight,X} from 'lucide-react';
import {BadgeMedallion} from './AchievementGallery';
import {REGIONS,mountainName,badgeSeed} from '../utils/achievementRegions';
import '../styles/mountainMap.css';

export default function MountainMap({badges=[],points=0}){
 const [region,setRegion]=useState('foundations'),[selectedId,setSelectedId]=useState(null);
 const dialog=useRef(null);
 const selected=badges.find(b=>b.id===selectedId),pieces=badges.filter(b=>(b.region||'foundations')===region);
 const explored=badges.filter(b=>b.unlocked).length,position=REGIONS.findIndex(([id])=>id===region);
 useEffect(()=>{if(selected&&!dialog.current?.open)dialog.current?.showModal();},[selectedId]);
 function close(){dialog.current?.close();setSelectedId(null)}
 return <section className="mountain-atlas" aria-label="Achievement mountain map">
  <header className="atlas-heading"><span className="eyebrow">An atlas of small victories</span><h2>Your world, uncovered.</h2><p>Every achievement reveals a piece of the map. Choose a mountain to plan your next expedition.</p></header>
  <div className="atlas-totals"><span><Flag size={15}/><strong>{explored} / {badges.length}</strong> climbed</span><span>{points.toLocaleString()} points earned</span></div>
  <label className="atlas-region-label">Explore a region<select aria-label="Map region" value={region} onChange={e=>setRegion(e.target.value)}>{REGIONS.map(([id,label])=>{const group=badges.filter(b=>(b.region||'foundations')===id);return <option key={id} value={id}>{label} · {group.filter(b=>b.unlocked).length}/{group.length} climbed</option>})}</select></label>
  <div className="atlas-legend"><span><i className="explored-key"/>Explored & climbed</span><span><i/>Uncharted</span></div>
  {!badges.length?<p role="status">Your expedition map is loading…</p>:<div className="atlas-pieces" aria-label={REGIONS[position][1]}>{pieces.map(badge=>{
   const seed=badgeSeed(badge.id),peak=35+seed%13;
   return <button key={badge.id+String(badge.unlocked)} className={'map-piece '+(badge.unlocked?'is-explored':'is-uncharted')} aria-haspopup="dialog" aria-label={`${mountainName(badge)}. ${badge.name}. ${badge.unlocked?'Explored and climbed':'Uncharted'}. View achievement details.`} onClick={()=>setSelectedId(badge.id)}>
    <svg className="piece-terrain" viewBox="0 0 180 160" aria-hidden="true"><path d="M0 136Q20 111 39 128T83 119T128 132T180 119V160H0Z" className="piece-hills"/><path d={`M17 128 54 65 77 101 104 ${peak} 164 131Z`} className="piece-mountain"/><path d={`M104 ${peak} 118 76 106 67 97 83 91 73Z`} className="piece-snow"/><path d={`M104 ${peak} 97 83 114 101 101 129M54 65 48 98 59 108 44 128`} className="piece-ridges"/>{badge.unlocked?<><path d={`M25 139Q56 114 69 118T91 97T104 ${peak}`} className="piece-route"/><path d={`M104 ${peak}v-18l14 4-14 5`} className="piece-flag"/></>:<path d="M17 78Q46 62 67 81T108 77T166 74M9 95Q38 81 59 96T110 92T174 93" className="piece-mist"/>}</svg>
    <BadgeMedallion badge={badge}/><span className="piece-name">{mountainName(badge)}</span><span className="piece-status">{badge.unlocked?<><Check size={11}/> Explored · Climbed</>:<><LockKeyhole size={10}/> Uncharted</>}</span>
   </button>
  })}</div>}
  <nav className="atlas-navigation" aria-label="Map regions"><button disabled={position===0} onClick={()=>setRegion(REGIONS[position-1][0])}><ChevronLeft size={16}/> Previous</button><span>{position+1} / {REGIONS.length}</span><button disabled={position===REGIONS.length-1} onClick={()=>setRegion(REGIONS[position+1][0])}>Next <ChevronRight size={16}/></button></nav>
  <dialog ref={dialog} className="mountain-dialog" onClose={()=>setSelectedId(null)} onCancel={e=>{e.preventDefault();close()}} onKeyDown={e=>{if(e.key==='Escape'){e.preventDefault();close()}}} onClick={e=>{if(e.target===e.currentTarget)close()}} aria-labelledby="mountain-dialog-title">
   {selected&&<div className="mountain-detail"><button className="mountain-dialog-close" aria-label="Close mountain details" onClick={close}><X size={22}/></button><BadgeMedallion badge={selected}/><span className="eyebrow">{selected.unlocked?'Explored and climbed':'Your next expedition'}</span><h2 id="mountain-dialog-title">{mountainName(selected)}</h2><h3>{selected.name}</h3><p>{selected.criteria}</p><progress max={selected.target} value={selected.unlocked?selected.target:selected.progress} aria-label={`${selected.name} progress`}/><small>{selected.unlocked?selected.target:selected.progress} / {selected.target}</small><blockquote>“{selected.flavor}”</blockquote>{selected.unlocked&&<p className="mountain-earned"><Check size={16}/> Climbed {new Date(selected.earned_at).toLocaleDateString(undefined,{timeZone:'America/Los_Angeles',month:'short',day:'numeric',year:'numeric'})}</p>}<button className="primary wide" onClick={close}>Back to the map</button></div>}
  </dialog>
 </section>;
}
