import React from 'react';
import {ArrowRight,Check,X} from 'lucide-react';
import {GOALS,INTERESTS,SKILLS} from '../../constants';

// First-visit setup, also reopened to edit the profile (then it can be closed).
export default function OnboardingModal({canClose,goal,interests,skills,error,busy,onGoal,onToggleInterest,onToggleSkill,onClose,onSubmit}){
 return <div className="overlay"><section className="modal onboarding" role="dialog" aria-modal="true" aria-labelledby="onboard-title">
  <span className="eyebrow">LET'S START WITH YOU</span>
  {canClose&&<button className="close" aria-label="Close profile" onClick={onClose}><X/></button>}
  <h2 id="onboard-title">Your next chapter.<br/><em>Your kind of things.</em></h2>
  <p>Choose a direction. We’ll help you find a small first step.</p>
  <form onSubmit={e=>{e.preventDefault();onSubmit()}}>
   <label htmlFor="goal">What brings you here?</label>
   <select id="goal" value={goal} onChange={e=>onGoal(e.target.value)}>{GOALS.map(g=><option key={g}>{g}</option>)}</select>
   <fieldset><legend>I'm curious about <small>Choose at least one</small></legend><div className="choice-tags">{INTERESTS.map(t=><button type="button" aria-pressed={interests.includes(t)} key={t} onClick={()=>onToggleInterest(t)}>{interests.includes(t)&&<Check size={14}/>} {t}</button>)}</div></fieldset>
   <fieldset><legend>I bring a little <small>Choose at least one</small></legend><div className="choice-tags">{SKILLS.map(t=><button type="button" aria-pressed={skills.includes(t)} key={t} onClick={()=>onToggleSkill(t)}>{skills.includes(t)&&<Check size={14}/>} {t}</button>)}</div></fieldset>
   {error&&<p role="alert" className="form-error">{error}</p>}
   <button className="primary wide" disabled={busy||!skills.length||!interests.length}>Find my one thing <ArrowRight size={18}/></button>
  </form>
  <small className="modal-foot">A fictional profile. A real little step. No login needed.</small>
 </section></div>
}
