import {supabase} from './auth.js';

export function createApiClient(getSession=()=>supabase?.auth.getSession()) {
 async function request(path, data, method = 'POST') {
  const {data:auth,error:authError} = await getSession() || {data:{session:null}};
  if(authError || !auth?.session?.access_token) throw new Error('Please log in to continue.');
  const headers={'Authorization':`Bearer ${auth.session.access_token}`};
  if(data!==undefined && !(data instanceof FormData))headers['Content-Type']='application/json';
  let response;
  try { response = await fetch(`/api${path}`, {method:data===undefined?'GET':method,headers,...(data===undefined?{}:{body:data instanceof FormData?data:JSON.stringify(data)})}); }
  catch { throw new Error('Cannot reach One Thing. Check that the backend is running, then try again.'); }
  let result;
  try { result = await response.json(); } catch {
    if ([502,503,504].includes(response.status)) throw new Error('Cannot reach One Thing. Check that the backend is running, then try again.');
    if (!response.ok) throw new Error(`The API request failed (${response.status}). Please try again.`);
    throw new Error('The server returned an unexpected response. Refresh the app and try again.');
  }
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
 return {achievementOptions:()=>request('/achievement-options'),recordEvent:data=>request('/activity/events',data),recommendations:filters=>queryRequest('/recommendations',filters),progressData:filters=>queryRequest('/progress/data',filters),catalogOptions:()=>request('/catalog/options'),catalogSearch:filters=>queryRequest('/catalog/opportunities',filters),analytics:filters=>queryRequest('/analytics',filters),recapNarrative:choices=>request('/recap/narrative',choices||{}),demoDate:data=>request('/demo/clock',data),feed:filters=>queryRequest('/opportunities',filters),saved:()=>request('/saved'),quests:()=>request('/quests'),progress:()=>request('/progress'),checkin:data=>request('/checkins',data),profile:data=>request('/profiles',data),save:(id,filters={})=>request('/saved',{opportunity_id:id,filters}),unsave:id=>request('/saved',{opportunity_id:id},'DELETE'),complete:(id,log={})=>request('/completions',{quest_id:id,...log})};
}

export const api=createApiClient();
