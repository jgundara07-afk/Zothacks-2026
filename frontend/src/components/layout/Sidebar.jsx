import React from 'react';
import {SlidersHorizontal} from 'lucide-react';
import {NAV_ITEMS} from '../../constants';

export default function Sidebar({page,savedCount,onHome,onNavigate,onEditProfile}){
 return <aside className="sidebar">
  <a className="brand" href="#" onClick={e=>{e.preventDefault();onHome()}}><span className="brand-mark">1</span>one thing<span className="brand-dot">.</span></a>
  <div className="side-label">A little progress, every day</div>
  <nav aria-label="Main navigation">{NAV_ITEMS.map(([name,Icon],i)=><button className={page===name?'nav active':'nav'} key={name} onClick={()=>onNavigate(name)}><span className="nav-index">{String(i+1).padStart(2,'0')}</span><Icon size={17}/>{name}{name==='Saved things'&&<span className="count">{savedCount}</span>}</button>)}</nav>
  <div className="sidebar-note"><h3>You don't need to do it <em>all.</em></h3><p>Just one thing that moves you a little forward.</p></div>
  <button className="profile" onClick={onEditProfile}><span className="avatar">A</span><span><strong>Alex's little journey</strong><small>Fictional demo profile</small></span><SlidersHorizontal size={16}/></button>
 </aside>
}
