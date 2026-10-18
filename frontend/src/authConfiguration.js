export function resolveAuthConfiguration(env = {}) {
  const url = env.VITE_SUPABASE_URL?.trim() || '';
  const key = env.VITE_SUPABASE_PUBLISHABLE_KEY?.trim() || env.VITE_SUPABASE_ANON_KEY?.trim() || '';
  if (!url || !key) return {url:'',key:'',error:'Supabase is not connected. Add the project URL and public key to frontend/.env.local, then restart the app.'};
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' && !(parsed.protocol === 'http:' && ['localhost','127.0.0.1'].includes(parsed.hostname))) throw new Error();
  } catch { return {url:'',key:'',error:'The Supabase project URL is invalid. Copy the Project URL from your Supabase dashboard.'}; }
  if (key.startsWith('sb_secret_')) return {url:'',key:'',error:'A secret key cannot be used in the browser. Use the publishable key from Supabase instead.'};
  return {url,key,error:null};
}
