import React from 'react';
import {ArrowRight,Check,X} from 'lucide-react';
import {GOALS,INTERESTS,SKILLS,OPENING_PHOTO,OPENING_HALFTONE} from '../../constants';

// First-visit setup, also reopened to edit the profile (then it can be closed).
// Composition follows design/references/iris-halftone-signin-reference.png: ghosted photo, crisp panel, halftone.
export default function OnboardingModal({canClose,goal,interests,skills,error,busy,onGoal,onToggleInterest,onToggleSkill,onClose,onSubmit}){
 return <div className="overlay opening" style={{'--opening-photo':`url(${OPENING_PHOTO})`}}><section className="modal onboarding" role="dialog" aria-modal="true" aria-labelledby="onboard-title">
  <div className="onboarding-form">
   <span className="eyebrow"><span className="mark">One thing</span> / 001</span>
   {canClose&&<button className="close" aria-label="Close profile" onClick={onClose}><X/></button>}
   <h2 id="onboard-title">Your next chapter.<br/>Your kind of <em>things.</em></h2>
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
  </div>
  <div className="onboarding-art" aria-hidden="true"><img src={OPENING_HALFTONE} alt=""/><span>33.6405° N<br/>117.8443° W</span></div>
 </section></div>
}
