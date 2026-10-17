import React from 'react';
import {ArrowRight,Check,Flag,Sprout} from 'lucide-react';
import Analytics from '../components/Analytics';

export default function ProgressPage({progress,analytics,onDiscover,onRecap}){
 return <>
  <section className="progress-panel"><div className="section-heading"><h2>Your trail so far</h2><Flag size={20}/></div>
   <div className="stats"><div><strong>{progress.points}</strong><span>points earned</span></div><div><strong>{progress.completed_count}</strong><span>quests completed</span></div><div><strong>{progress.saved_count}</strong><span>things saved</span></div></div>
   <h3>Little wins, real progress</h3>
   {progress.activity.length
    ?progress.activity.map(a=><div className="activity" key={a.id||a.quest_id}><span className="tick"><Check size={18}/></span><div><strong>{a.title}</strong><small>{new Date(a.completed_at).toLocaleDateString(undefined,{month:'short',day:'numeric'})} · Quest completed</small></div><b>+{a.points}</b></div>)
    :<div className="empty"><Sprout/><h3>Your first step is waiting.</h3><p>Save an opportunity and finish its quest to start your climb.</p><button className="primary" onClick={onDiscover}>Find my one thing <ArrowRight size={17}/></button></div>}
  </section>
  <Analytics data={analytics} onRecap={onRecap}/>
 </>
}
