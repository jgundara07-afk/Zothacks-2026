import React,{useEffect,useState} from 'react';
import {api} from '../api';
export default function WorkLog({kind,minutes,setMinutes,outcome,setOutcome}){
 const [options,setOptions]=useState([]);
 useEffect(()=>{let active=true;api.achievementOptions().then(data=>{if(active)setOptions(data.outcomes)}).catch(()=>{});return()=>{active=false}},[]);
 const restricted={applied:['Job','Internship'],certification_completed:['Online course','Certification'],event_attended:['Local event','Networking','Networking event','Campus event','Club','Campus initiative']};
 return <details className="work-log"><summary>Log time or an outcome (optional)</summary><label>Time you actually spent, in minutes<input type="number" min="1" max="1440" placeholder="Leave blank if not tracked" value={minutes} onChange={e=>setMinutes(e.target.value)}/></label><label>What else did you finish?<select value={outcome} onChange={e=>setOutcome(e.target.value)}><option value="">No additional outcome</option>{options.filter(o=>!restricted[o.value]||restricted[o.value].includes(kind)).map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select></label><small>Log only what you actually did. Preparing for an application, certification or event does not mean you submitted, finished or attended it.</small></details>;
}
