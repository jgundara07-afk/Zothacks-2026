import catalog from '../../../shared/interest_catalog.json' with {type:'json'};

export {catalog as interestCatalog};
export function searchInterests(groups,query='',category='All categories'){
 const terms=query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
 const values=groups.filter(g=>category==='All categories'||g.name===category).flatMap(g=>g.interests);
 return [...new Set(values)].filter(value=>terms.every(term=>value.toLocaleLowerCase().includes(term)));
}

// Shuffle within categories, then alternate categories so the first page stays varied.
export function mixInterests(groups,random=Math.random){
 const shuffle=items=>{const out=[...items];for(let i=out.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[out[i],out[j]]=[out[j],out[i]]}return out};
 const buckets=shuffle(groups.map(group=>shuffle(group.interests)));
 const result=[],seen=new Set();
 for(let i=0;buckets.some(bucket=>i<bucket.length);i++)for(const bucket of buckets){const value=bucket[i];if(value&&!seen.has(value)){seen.add(value);result.push(value)}}
 return result;
}
