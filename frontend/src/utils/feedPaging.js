export function mergeFeedPage(previous, page) {
 const opportunities=[...new Map([...(previous?.opportunities||[]),...page.opportunities].map(o=>[o.id,o])).values()];
 return {...page,opportunities};
}
export function nextFeedOffset(feed){
 return feed?(feed.offset||0)+(feed.page_count??feed.opportunities.length):0;
}
