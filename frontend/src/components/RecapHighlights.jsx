import React,{useState} from 'react';
import {Share2} from 'lucide-react';
import ActivityWitness,{publishAchievements} from './ActivityWitness';
import {api} from '../api';
export default function RecapHighlights({result,onRecorded}){
 const [status,setStatus]=useState('');const rows=result?.highlights||[];
 async function share(){
  const text='My OneThing highlights\n'+rows.map((row,i)=>`${i+1}. ${row.title}`).join('\n')+'\nOne useful step at a time.';
  const sharing=navigator.share?navigator.share({title:'My OneThing field notes',text}):navigator.clipboard?.writeText(text);
  api.recordEvent({event:'share_click',recap_id:result.recap_id}).then(data=>{publishAchievements(data.achievements);onRecorded?.(data.achievements)}).catch(()=>{});
  try{await sharing;setStatus(navigator.share?'Share dialog finished.':sharing?'Highlights copied. Paste them wherever you want to share.':'Select and copy the highlights above to share them.')}catch(error){setStatus(error.name==='AbortError'?'Share cancelled.':'Sharing is unavailable. You can copy the highlights above.')}
 }
 if(!result)return <p role="status">Your highlight card will be ready when this recap finishes.</p>;
 if(!rows.length)return <p>Complete a quest in this period to start your highlight reel.</p>;
 return <ActivityWitness event="highlight_view" recapId={result.recap_id} onRecorded={onRecorded}><section className="highlight-card"><span className="eyebrow">Your field notes</span><h2>Your top {rows.length} quests</h2><p>A few useful steps worth remembering.</p><ol>{rows.map((row,i)=><li key={i}>{row.title}<small>{row.date}</small></li>)}</ol><button className="primary wide" onClick={share}><Share2 size={16}/> Share highlights</button>{status&&<p role="status">{status}</p>}</section></ActivityWitness>;
}
