import React from 'react';
import {Check,Clock3,X} from 'lucide-react';
import Print from '../Print';

// A quest's checklist. Completing is only enabled once every step is ticked.
export default function QuestModal({quest,color,checked,error,busy,onToggleStep,onClose,onComplete}){
 return <div className="overlay"><section className="modal quest" role="dialog" aria-modal="true" aria-labelledby="quest-title">
  <button className="close" aria-label="Close quest" onClick={onClose}><X/></button>
  <Print id={quest.opportunity_id} color={color}/>
  <div className="quest-body">
   <span className="eyebrow">Your little first step</span>
   <h2 id="quest-title">{quest.title}</h2>
   <div className="quest-meta"><span><Clock3 size={14}/>{quest.minutes} min</span><span>{quest.difficulty}</span>{quest.daily&&<span>Daily practice</span>}<span>+{quest.points} points</span></div>
   <p>{quest.description}</p>
   <div className="checklist">{quest.steps.map((step,i)=><label key={step}><input type="checkbox" checked={checked.includes(i)} onChange={()=>onToggleStep(i)}/><span>{step}</span></label>)}</div>
   {error&&<p role="alert" className="form-error">{error}</p>}
   <button className="primary wide" disabled={busy||quest.completed||checked.length!==quest.steps.length} onClick={onComplete}>{quest.completed?'Already completed':busy?'Saving your step…':'I did my one thing'}<Check size={18}/></button>
   <small className="modal-foot">This is self-reported. Take your time and do the steps offline.</small>
  </div>
 </section></div>
}
