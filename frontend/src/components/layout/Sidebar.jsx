import React from 'react';
import {SlidersHorizontal} from 'lucide-react';
import {NAV_ITEMS} from '../../constants';

export default function Sidebar({page,savedCount,onHome,onNavigate,onEditProfile}){
 return <aside className="sidebar">
  <a className="brand" href="#" onClick={e=>{e.preventDefault();onHome()}}><span className="brand-mark">1<span>✳</span></span>one thing<span className="brand-dot">.</span></a>
  <div className="side-label">A LITTLE PROGRESS, EVERY DAY</div>
  <nav aria-label="Main navigation">{NAV_ITEMS.map(([name,Icon])=><button className={page===name?'nav active':'nav'} key={name} onClick={()=>onNavigate(name)}><Icon size={19}/>{name}{name==='Saved things'&&<span className="count">{savedCount}</span>}</button>)}</nav>
  <div className="sidebar-note"><span className="small-star">✳</span><h3>You don't need to<br/>do it all.</h3><p>Just one thing that moves<br/>you a little forward.</p><span className="note-squiggle">⤳</span></div>
  <button className="profile" onClick={onEditProfile}><span className="avatar">A</span><span><strong>Alex's little journey</strong><small>Fictional demo profile</small></span><SlidersHorizontal size={16}/></button>
 </aside>
}
