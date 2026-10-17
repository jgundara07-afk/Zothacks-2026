import React from 'react';
import {ArrowRight,Pencil} from 'lucide-react';
import {MOODS,EFFORTS} from '../constants';

// "How are you feeling?" box on Discover. Shows a summary once today's check-in is saved.
export default function DailyCheckin({checkin,hasProfile,streak,mood,effort,editing,busy,onMood,onEffort,onEdit,onSubmit}){
 return <section className="daily-checkin" aria-labelledby="checkin-title">
  <div className="checkin-heading"><div><span className="eyebrow">TODAY, AT YOUR PACE</span><h2 id="checkin-title">How are you feeling?</h2></div><span className="streak-badge">✳ {streak||0} day streak</span></div>
  {checkin&&!editing
   ?<div className="checkin-summary"><p>{checkin.mood === 'Low' ? 'Taking it gently.' : checkin.mood === 'Good' ? 'A little energy to explore.' : 'One step at a time.'} Your feed is set to <strong>{checkin.effort==='small'?'small, 2-minute steps':'bigger, 10–20 minute steps'}</strong>.</p><button className="text-link" onClick={onEdit}>Change today's check-in <Pencil size={14}/></button></div>
   :<form onSubmit={e=>{e.preventDefault();onSubmit()}}>
    <fieldset><legend>My mood today</legend><div className="choice-tags">{MOODS.map(([value,label])=><button type="button" key={value} aria-pressed={mood===value} onClick={()=>onMood(value)}>{label}</button>)}</div></fieldset>
    <fieldset><legend>How much feels right?</legend><div className="choice-tags">{EFFORTS.map(([value,label])=><button type="button" key={value} aria-pressed={effort===value} onClick={()=>onEffort(value)}>{label}</button>)}</div></fieldset>
    <button className="primary" disabled={busy||!hasProfile}>Set my pace <ArrowRight size={16}/></button>
   </form>}
  <small>No pressure. A small completed step counts just as much toward your streak.</small>
 </section>
}
