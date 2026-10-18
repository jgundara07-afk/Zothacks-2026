import {normalizeEmail} from './emailPolicy.js';
import {supabase,authConfigurationError} from './auth.js';

function friendly(error, mode) {
 const code=error?.code;
 if(code==='user_already_exists'||code==='email_exists')return 'An account may already exist for this email. Try logging in.';
 if(code==='invalid_credentials')return 'Email or password is incorrect. Please try again.';
 if(code==='email_not_confirmed')return 'Verify your email using the link we sent, then log in.';
 if(code==='email_address_not_authorized')return 'Verification email cannot be sent to this address yet. Email delivery needs to be configured by the OneThing team.';
 if(code==='weak_password')return 'Choose a stronger password with at least 8 characters.';
 if(code==='over_email_send_rate_limit')return 'Verification emails are temporarily limited. Check your inbox for an earlier link, or wait before trying again.';
 if(code==='over_request_rate_limit')return 'Too many requests from this network. Please wait a few minutes before trying again.';
 return error?.message || (mode==='signup'?'Could not create your account. Try again.':'Could not log in. Try again.');
}
function authIssue(error,mode){
 const issue=new Error(friendly(error,mode));
 issue.code=error?.code;
 return issue;
}
function requireClient(client){if(!client)throw new Error(authConfigurationError || 'Authentication is unavailable. Please try again later.')}

export async function register({name,email,password,confirmation,redirectTo},client=supabase){
 requireClient(client);
 const address=normalizeEmail(email);
 if(!name?.trim())throw new Error('Enter your name.');
 if(password.length<8)throw new Error('Use at least 8 characters for your password.');
 if(password!==confirmation)throw new Error('Passwords do not match.');
 const {data,error}=await client.auth.signUp({email:address,password,options:{data:{name:name.trim()},emailRedirectTo:redirectTo}});
 if(error)throw authIssue(error,'signup');
 if(data?.session){await client.auth.signOut();throw new Error('Email verification must be enabled before new accounts can use OneThing.')}
 return data?.user?.identities?.length===0
  ? 'If this address already has an account, log in instead. Otherwise, check your inbox for a verification link.'
  : `Check ${address} for a verification link, then return here to log in.`;
}

export async function login({email,password},client=supabase){
 requireClient(client);
 const address=normalizeEmail(email);
 const {data,error}=await client.auth.signInWithPassword({email:address,password});
 if(error)throw authIssue(error,'login');
 if(!data?.session?.access_token||!data?.session?.user?.id)throw new Error('Could not verify your session. Please try again.');
 return data.session;
}

export async function startGoogleSignIn({redirectTo},client=supabase){
 requireClient(client);
 const {data,error}=await client.auth.signInWithOAuth({provider:'google',options:{redirectTo}});
 if(error)throw authIssue(error,'login');
 if(!data?.url)throw new Error('Could not start Google sign-in. Please try again.');
 return data.url;
}

export async function resendVerification({email,redirectTo},client=supabase){
 requireClient(client);
 const address=normalizeEmail(email);
 const {error}=await client.auth.resend({type:'signup',email:address,options:{emailRedirectTo:redirectTo}});
 if(error)throw authIssue(error,'signup');
 return `If ${address} has an unverified account, a new verification link is on its way.`;
}

export async function logout(client=supabase){
 requireClient(client);
 const {error}=await client.auth.signOut();
 if(error)throw authIssue(error,'login');
}
