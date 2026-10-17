import React,{useState} from 'react';
import {REGIONS,badgeSeed} from '../utils/achievementRegions';
import {Footprints,Percent,Armchair,Dumbbell,ScanText,Sprout,Compass,Archive,Handshake,Flag,LockKeyhole} from 'lucide-react';
const art={
 'first-step':[Footprints,'#d4ae64',6], 'one-percent':[Percent,'#82ada0',12],
 'couch-bound':[Armchair,'#b49bcc',8], 'heavy-lifter':[Dumbbell,'#dc9073',5],
 'algorithm-whisperer':[ScanText,'#8fb4ce',4], 'touch-grass':[Sprout,'#a4b576',9],
 renaissance:[Compass,'#dfba72',16], visionary:[Archive,'#bd93a0',7],
 'warm-intro':[Handshake,'#d1a379',10], 'base-camp':[Flag,'#edce85',3],
};
export function BadgeMedallion({badge,index=0}){
 const seed=badgeSeed(badge.id);
 const symbols=[Footprints,Percent,Armchair,Dumbbell,ScanText,Sprout,Compass,Archive,Handshake,Flag];
 const [Icon,color,sides]=art[badge.id]||[symbols[seed%symbols.length],`hsl(${seed%360} 35% ${62+seed%12}%)`,5+seed%12];
 const points=Array.from({length:sides},(_,i)=>{const a=(i/sides*2-0.5)*Math.PI;return `${50+44*Math.cos(a)},${50+44*Math.sin(a)}`}).join(' ');
 return <div className={'badge-medallion '+(badge.unlocked?'earned':'locked')} style={{'--badge-color':color}} aria-hidden="true">
  <svg viewBox="0 0 100 110"><path d="M31 72 24 107 49 95 73 107 67 72" className="badge-ribbon"/><polygon points={points} className="badge-frame"/><circle cx="50" cy="50" r="33" className="badge-inner"/><path d="M32 78 Q50 86 68 78" className="badge-engraving"/></svg>
  <Icon className="badge-symbol" strokeWidth={1.4}/><span className="badge-number">{String(badge.number||index+1).padStart(2,'0')}</span>
 </div>;
}
export default function AchievementGallery({badges=[],monthly=false,periodLabel=null}){
 const scope=periodLabel||(monthly?'month':null);
 const [region,setRegion]=useState('all');
 const shown=region==='all'?badges:badges.filter(b=>(b.region||'foundations')===region);
 const count=badges.filter(b=>b.unlocked).length;
 return <section className="achievement-gallery" aria-label="Achievement badges">
  <div className="achievement-heading"><div><span className="eyebrow">Marks of the climb</span><h2>Your badge collection</h2></div><span>{count} / {badges.length} earned</span></div>
  <p className="badge-intro">Small victories, made permanent. Open a badge to discover its story.{scope?` Your collection is lifetime; new badges from this ${scope} are marked below.`:''}</p>
  <label className="atlas-region-label">Badge region<select aria-label="Badge region" value={region} onChange={e=>setRegion(e.target.value)}><option value="all">All regions</option>{REGIONS.map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
  {!badges.length?<p>Your badges will appear when progress finishes loading.</p>:<div className="badge-grid">{shown.map((badge,index)=><details className={'badge-card '+(badge.unlocked?'is-earned':'is-locked')} key={badge.id}>
   <summary><BadgeMedallion badge={badge} index={index}/><span className="badge-name">{badge.name}</span><span className="badge-state">{badge.unlocked?(scope&&badge.earned_in_period?`Earned this ${scope}`:'Unlocked'):<><LockKeyhole size={11}/> Locked</>}</span></summary>
   <div className="badge-details"><p>{badge.criteria}</p><progress aria-label={`${badge.name} progress`} value={badge.unlocked?badge.target:badge.progress} max={badge.target}/><small>{badge.unlocked?badge.target:badge.progress} / {badge.target}{badge.id==='base-camp'?' points':''}</small><p className="badge-flavor">“{badge.flavor}”</p>{badge.earned_at&&<small>Earned {new Date(badge.earned_at).toLocaleDateString(undefined,{timeZone:'America/Los_Angeles',month:'short',day:'numeric',year:'numeric'})}</small>}</div>
  </details>)}</div>}
 </section>;
}
