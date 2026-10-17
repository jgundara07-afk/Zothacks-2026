async function request(path, data, method = 'POST') {
  let response;
  try { response = await fetch(`/api${path}`, data === undefined ? {} : {method,...(data instanceof FormData?{body:data}:{headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})}); }
  catch { throw new Error('Cannot reach One Thing. Check that the backend is running, then try again.'); }
  let result;
  try { result = await response.json(); } catch { throw new Error('The server returned an unexpected response. Please try again.'); }
  if (!response.ok) throw new Error(result.error || 'Something went wrong. Please try again.');
  return result;
}
function queryRequest(path, filters = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null) continue;
    for (const item of Array.isArray(value) ? value : [value]) query.append(key, String(item));
  }
  return request(`${path}?${query}`);
}
export const api = {recommendations:filters=>queryRequest('/recommendations',filters),progressData:filters=>queryRequest('/progress/data',filters),catalogOptions:()=>request('/catalog/options'),catalogSearch:filters=>queryRequest('/catalog/opportunities',filters),analytics:filters=>queryRequest('/analytics',filters),demoDate:data=>request('/demo/clock',data),feed:filters=>queryRequest('/opportunities',filters),saved:()=>request('/saved'),quests:()=>request('/quests'),progress:()=>request('/progress'),checkin:data=>request('/checkins',data),profile:data=>request('/profiles',data),save:id=>request('/saved',{opportunity_id:id}),unsave:id=>request('/saved',{opportunity_id:id},'DELETE'),complete:id=>request('/completions',{quest_id:id})};
