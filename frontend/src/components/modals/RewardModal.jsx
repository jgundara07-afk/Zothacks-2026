import React from 'react';
import {ArrowRight} from 'lucide-react';

// Celebration shown right after a quest is completed: a stamp lands on the page.
export default function RewardModal({points,onSeeClimb,onClose}){
 const today=new Date().toLocaleDateString(undefined,{month:'short',day:'numeric'});
 return <div className="overlay"><section className="modal celebration" role="dialog" aria-modal="true" aria-labelledby="reward-title">
  <div className="reward-stamp" aria-hidden="true"><span>Quest</span><strong>Complete</strong><span>{today}</span></div>
  <span className="eyebrow">A little win worth celebrating</span>
  <h2 id="reward-title">Look at you,<br/>moving <em>forward.</em></h2>
  <p>You turned a little time into something good.</p>
  <div className="reward-points">+{points}<span>points for your journey</span></div>
  <button autoFocus className="primary wide" onClick={onSeeClimb}>See my climb <ArrowRight size={18}/></button>
  <button className="text-link" onClick={onClose}>Keep exploring</button>
 </section></div>
}
