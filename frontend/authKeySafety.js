// Build-time guard: VITE_* values can be read from the shipped JavaScript bundle.
export function assertPublicSupabaseKey(name, value) {
  if (!value) return;
  let serviceRole = value.startsWith('sb_secret_');
  if (!serviceRole && value.split('.').length === 3) {
    try {
      const payload = JSON.parse(Buffer.from(value.split('.')[1], 'base64url').toString('utf8'));
      serviceRole = payload.role === 'service_role';
    } catch { /* Supabase will report an invalid public key at runtime. */ }
  }
  if (serviceRole) throw new Error(`${name} contains a Supabase secret/service-role key. Use a publishable or anon key instead.`);
}
