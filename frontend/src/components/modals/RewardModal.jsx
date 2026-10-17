import React from 'react';
import {ArrowRight} from 'lucide-react';

// Celebration shown right after a quest is completed.
export default function RewardModal({points,onSeeClimb,onClose}){
 return <div className="overlay"><section className="modal celebration" role="dialog" aria-modal="true" aria-labelledby="reward-title">
  <svg className="reward-mountain" viewBox="0 0 140 100" aria-hidden="true"><path d="M10 90 L70 12 L130 90 M50 40 L70 48 L82 30" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round"/><circle cx="70" cy="12" r="7" fill="#dab655"/></svg>
  <span className="eyebrow">A LITTLE WIN WORTH CELEBRATING</span>
  <h2 id="reward-title">Look at you,<br/><em>moving forward.</em></h2>
  <p>You turned a little time into something good.</p>
  <div className="reward-points">+{points}<span>points for your journey</span></div>
  <button autoFocus className="primary wide" onClick={onSeeClimb}>See my climb <ArrowRight size={18}/></button>
  <button className="text-link" onClick={onClose}>Keep exploring</button>
 </section></div>
}
