import React from 'react';
import {ArrowRight,Flag} from 'lucide-react';

// The climber dot moves from the trail start toward the flag as points go from 0 to 500.
export default function MountainClimb({progress,onSeeProgress}){
 const climb=Math.min(1,progress.points/500);
 return <section className="climb"><div className="section-heading"><h2>Your little climb</h2><Flag size={17}/></div><p>One step closer is still closer.</p>
  <svg className="mountain" viewBox="0 0 260 190" role="img" aria-label={`${progress.points} points earned on your mountain climb`}><path d="M0 180 L63 87 L99 124 L149 37 L260 180" fill="#e0e6d7"/><path d="M149 37 L126 77 L146 69 L163 83 L175 75Z" fill="#fbfaf5"/><path d="M0 180 L63 87 L87 123 L113 160 L140 180" fill="#ced9c4"/><path d="M42 179 Q94 161 90 143 T126 108 T149 48" stroke="#879a78" strokeWidth="2" strokeDasharray="4 5" fill="none"/><path d="M149 38 V16 L171 21 L149 29" fill="#d28862" stroke="#53664d" strokeWidth="1.5"/><circle className="climber" cx={90+59*climb} cy={143-95*climb} r="10" fill="#f1c56c" stroke="#fbfaf5" strokeWidth="4"/><text x="15" y="65" fontSize="20" fill="#c8a854">✳</text><path d="M203 114 l5 -5 m-5 0 l5 5" stroke="#9caa8c"/></svg>
  <div className="climb-stats"><strong>{progress.points}<small> points</small></strong><span>Trail {Math.floor(progress.points/100)+1}</span></div>
  <div className="progress-track"><span style={{width:`${progress.points%100}%`}}/></div>
  <small>{100-progress.points%100} points to your next milestone</small>
  <button className="text-link" onClick={onSeeProgress}>See your progress <ArrowRight size={15}/></button>
 </section>
}
