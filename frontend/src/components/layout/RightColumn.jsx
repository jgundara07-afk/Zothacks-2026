import React from 'react';
import {Pencil,Plus} from 'lucide-react';
import MountainClimb from '../MountainClimb';

export default function RightColumn({progress,interests,onSeeProgress,onEditProfile}){
 return <aside className="right-column">
  <section className="streak-panel"><span className="eyebrow">Keep showing up for you</span><h2><span className="streak-number">{progress.streak||0}</span> day streak</h2><p>{progress.active_today?"Today's step is done. See you tomorrow.":'Complete one quest today to keep your momentum.'}</p><small>Best: {progress.longest_streak||0} days · Pacific time</small><p className="streak-kindness">Missed a day? Start fresh. Your progress stays yours.</p></section>
  <MountainClimb progress={progress} onSeeProgress={onSeeProgress}/>
  <section className="your-mix"><div className="section-heading"><h2>Your kind of things</h2><button aria-label="Edit your interests" onClick={onEditProfile}><Pencil size={15}/></button></div><p>A little bit of what makes you, you.</p><div className="tags">{interests.map(t=><span key={t}>{t}</span>)}</div><button className="text-link" onClick={onEditProfile}>Fine-tune your mix <Plus size={15}/></button></section>
  <div className="quote">“You don't have to see the whole staircase. Just take the first <em>step.</em>”<span>A little wisdom for the way</span></div>
 </aside>
}
