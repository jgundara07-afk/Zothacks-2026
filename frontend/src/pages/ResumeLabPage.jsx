import React,{useState} from 'react';
import {ArrowRight,Sparkles,FileText,Check} from 'lucide-react';
import {api} from '../api';

export default function ResumeLabPage({onExplore}){
 const [text,setText]=useState(''),[role,setRole]=useState('Software developer'),[result,setResult]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function analyze(e){e.preventDefault();setBusy(true);setError('');try{setResult(await api.resume({text,role}))}catch(e){setError(e.message)}finally{setBusy(false)}}
 async function loadFile(e){const file=e.target.files?.[0];if(!file)return;if(file.size>120000||!file.name.toLowerCase().endsWith('.txt')){setError('Choose a .txt file under 120 KB. You can paste text from a PDF instead.');return}try{const content=await file.text();if(content.length>30000)throw new Error('Keep text under 30,000 characters.');setText(content);setResult(null);setError('')}catch(e){setError(e.message)}}
 return <section className="resume-lab"><div className="section-heading"><h2>A little direction for your next chapter</h2><FileText size={20}/></div><p>Your experience is a starting point. Find skills to practice for a fictional target role.</p>
  <div className="local-label"><Check size={14}/> Local keyword demo · no external AI · text is not stored</div>
  <form onSubmit={analyze}>
   <label htmlFor="target-role">A role I'm curious about</label>
   <select id="target-role" value={role} onChange={e=>{setRole(e.target.value);setResult(null)}}>{['Software developer','Product designer','Community organizer'].map(r=><option key={r}>{r}</option>)}</select>
   <label htmlFor="resume-text">Paste resume text</label>
   <textarea id="resume-text" value={text} maxLength={30000} rows={9} onChange={e=>{setText(e.target.value);setResult(null)}} placeholder="Try: Built a React app using JavaScript. Wrote documentation and presented it to my class."/>
   <label htmlFor="resume-file">Or choose a plain text (.txt) resume</label>
   <input id="resume-file" type="file" accept=".txt,text/plain" onChange={loadFile}/>
   <small>Use fictional text for the shared demo. Remove contact details before pasting. For PDF or Word files, copy and paste the text.</small>
   {error&&<p className="form-error" role="alert">{error}</p>}
   <button className="primary" disabled={busy||!text.trim()}>{busy?'Finding a starting point…':'Find my next skills'}<Sparkles size={16}/></button>
  </form>
  {result&&<section className="resume-results" aria-live="polite"><h3>Your starting point</h3><p>For the sample <strong>{result.role}</strong> pathway</p>
   <div className="resume-result-grid"><div><span className="eyebrow">KEYWORDS WE FOUND</span><div className="tags">{result.found_skills.length?result.found_skills.map(s=><span key={s}>✓ {s}</span>):<p>No recognized skill keywords yet.</p>}</div></div><div><span className="eyebrow">POSSIBILITIES TO EXPLORE</span><div className="tags">{result.gaps.length?result.gaps.map(s=><span key={s}>{s}</span>):<p>All template skills have a keyword match.</p>}</div></div></div>
   <p className="method-note">{result.method}</p>
   {result.recommendations.length>0&&<button className="primary" onClick={()=>onExplore(result.gaps)}>Explore {result.recommendations.length} matching opportunities <ArrowRight size={16}/></button>}
  </section>}
 </section>
}
