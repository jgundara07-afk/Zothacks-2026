async function request(path, data) {
  let response;
  try { response = await fetch(`/api${path}`, data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); }
  catch { throw new Error('Cannot reach One Thing. Check that the backend is running, then try again.'); }
  let result;
  try { result = await response.json(); } catch { throw new Error('The server returned an unexpected response. Please try again.'); }
  if (!response.ok) throw new Error(result.error || 'Something went wrong. Please try again.');
  return result;
}
export const api = {feed:()=>request('/opportunities'),quests:()=>request('/quests'),progress:()=>request('/progress'),profile:data=>request('/profiles',data),save:id=>request('/saved',{opportunity_id:id}),complete:id=>request('/completions',{quest_id:id})};
