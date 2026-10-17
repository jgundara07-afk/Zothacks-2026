import catalog from '../../../shared/interest_catalog.json' with {type:'json'};

export {catalog as interestCatalog};
export function searchInterests(groups,query='',category='All categories'){
 const terms=query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
 const values=groups.filter(g=>category==='All categories'||g.name===category).flatMap(g=>g.interests);
 return [...new Set(values)].filter(value=>terms.every(term=>value.toLocaleLowerCase().includes(term)));
}
