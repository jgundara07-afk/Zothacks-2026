import React,{useState,useId} from 'react';
import {interestCatalog,searchInterests} from '../utils/interests';
import {toggleSelection} from '../utils/preferences';
import options from '../../../shared/preferences.json';
import {scenePhoto,INTEREST_SCENES} from '../utils/photos';
import {Check} from 'lucide-react';

export default function InterestPicker({value,onChange,images=false,label='Interests',help='Choose up to ten. Match any selected interest.'}){
 const [query,setQuery]=useState(''),[category,setCategory]=useState('All categories'),[limit,setLimit]=useState(60);
 const id=useId(),choices=searchInterests(interestCatalog.groups,query,category);
 const max=options.max_selected_interests;
 const toggle=interest=>onChange(toggleSelection(value,interest,max));
 const groupScenes={'Technology & Computer Science':'code','Business & Entrepreneurship':'finance','Design & Creative':'sketch','Science & Research':'lab','Education & Personal Development':'library','Health, Fitness & Sports':'sports','Finance & Investing':'finance','Social Impact & Community':'friends','Lifestyle, Travel & Culture':'map','Gaming, Media & Entertainment':'chess','Environment & Sustainability':'garden','Engineering & Making':'maker'};
 const photo=interest=>scenePhoto(INTEREST_SCENES[interest]||groupScenes[interestCatalog.groups.find(g=>g.interests.includes(interest))?.name]||'train',interest);
 return <fieldset className="preference-field interest-picker"><legend>{label} <span className="selection-counter">{value.length}/{max}</span></legend><p className="field-help">{help}</p>
  {value.length>0&&<div className="choice-tags" aria-label="Selected interests">{value.map(interest=><button key={interest} type="button" aria-label={`Remove ${interest}`} onClick={()=>toggle(interest)}>{interest} ×</button>)}</div>}
  <div className="feed-filters"><label htmlFor={id+'-search'}>Search interests<input id={id+'-search'} type="search" placeholder="Try robotics, cooking, or investing" value={query} onChange={e=>{setQuery(e.target.value);setLimit(60)}}/></label><label htmlFor={id+'-category'}>Category<select id={id+'-category'} value={category} onChange={e=>{setCategory(e.target.value);setLimit(60)}}><option>All categories</option>{interestCatalog.groups.map(group=><option key={group.name}>{group.name}</option>)}</select></label></div>
  <p className="field-help" role="status">{choices.length} interests found{value.length>=max?' · Limit reached; remove one to choose another.':''}</p><div className={images?'ob-tiles':'preference-choices'} role="group" aria-label="Interest choices">{choices.slice(0,limit).map(interest=>images?<button key={interest} type="button" className="ob-tile" aria-pressed={value.includes(interest)} disabled={value.length>=max&&!value.includes(interest)} onClick={()=>toggle(interest)} style={{'--tile':`url(${photo(interest)})`}}><span>{interest}</span>{value.includes(interest)&&<i className="ob-seal"><Check size={13}/></i>}</button>:<label key={interest} className={value.includes(interest)?'selected':''}><input type="checkbox" checked={value.includes(interest)} disabled={value.length>=max&&!value.includes(interest)} onChange={()=>toggle(interest)}/><span>{interest}</span></label>)}</div>
  {!choices.length&&<p>No interests match this search. Try another term or category.</p>}{limit<choices.length&&<button className="text-link" type="button" onClick={()=>setLimit(n=>n+60)}>Show more interests</button>}
 </fieldset>;
}
