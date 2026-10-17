import React from 'react';
import {DIFFICULTIES,MODES,GOAL_FILTERS,SKILL_FILTERS} from '../constants';

function FilterSelect({label,value,options,onChange}){
 return <label>{label}<select value={value} onChange={e=>onChange(e.target.value)}>{options.map(v=><option key={v}>{v}</option>)}</select></label>
}

// The dropdown filters under the topic pills on Discover.
export default function FeedFilters({all,filters,onFilter,onReset}){
 return <>
  <div className="feed-filters">
   <FilterSelect label="Quest difficulty" value={filters.difficulty} options={DIFFICULTIES} onChange={v=>onFilter('difficulty',v)}/>
   <FilterSelect label="Opportunity type" value={filters.source} options={['All sources',...new Set(all.map(o=>o.kind))]} onChange={v=>onFilter('source',v)}/>
   <FilterSelect label="Where" value={filters.mode} options={MODES} onChange={v=>onFilter('mode',v)}/>
   <FilterSelect label="My goal" value={filters.goal} options={GOAL_FILTERS} onChange={v=>onFilter('goal',v)}/>
   <FilterSelect label="Skill to practice" value={filters.skill} options={SKILL_FILTERS} onChange={v=>onFilter('skill',v)}/>
   <button className="text-link" onClick={onReset}>Reset filters</button>
  </div>
  {filters.gapSkills.length>0&&<p className="gap-filter">Exploring resume keyword gaps: {filters.gapSkills.join(', ')} <button onClick={()=>onFilter('gapSkills',[])}>Clear</button></p>}
 </>
}
