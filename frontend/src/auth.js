import {createClient} from '@supabase/supabase-js';
import {resolveAuthConfiguration} from './authConfiguration.js';
export {normalizeEmail,acceptedProviders} from './emailPolicy.js';

const {url,key,error}=resolveAuthConfiguration(import.meta.env);
export const authConfigurationError = error;
export const authConfigured = !error;
export const supabase = authConfigured ? createClient(url, key, {
  auth: {persistSession: true, autoRefreshToken: true, detectSessionInUrl: true},
}) : null;
