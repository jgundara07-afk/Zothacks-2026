import React from 'react';
import choices from '../../../shared/catalog_filters.json';

export const emptyMetadataFilters={experience:'Any',cost:'Any',prerequisites:'Any',duration_quality:'Any',schedule:'Any',max_minutes:''};
export function metadataQuery(filters){
 return Object.fromEntries(Object.entries(filters).filter(([,value])=>value!=='Any'&&value!=='').map(([key,value])=>[key,key==='max_minutes'?Number(value):value]));
}
export default function MetadataFilters({value,onChange}){
 const fields=[['experience','Experience level','experience_levels'],['cost','Cost','costs'],['prerequisites','Prerequisites','prerequisite_statuses'],['duration_quality','Time certainty','duration_qualities'],['schedule','Schedule','schedules']];
 return <fieldset><legend>A closer fit</legend><p className="field-help">Unknown details only match when you choose Unknown. Experience and difficulty are estimates; verify eligibility at the source.</p><div className="feed-filters">{fields.map(([key,label,option])=><label key={key}>{label}<select value={value[key]} onChange={e=>onChange({...value,[key]:e.target.value})}><option>Any</option>{choices[option].map(v=><option key={v}>{v}</option>)}</select></label>)}<label>Maximum total minutes<input type="number" min="1" step="1" placeholder="No limit" value={value.max_minutes} onChange={e=>onChange({...value,max_minutes:e.target.value})}/></label></div></fieldset>;
}
