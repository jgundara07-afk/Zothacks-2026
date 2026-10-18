import React,{useState} from 'react';
import {ArrowRight,Eye,EyeOff} from 'lucide-react';
import {authConfigured,authConfigurationError} from '../auth';
import {register,login,resendVerification} from '../authFlow';

const verificationRedirectTo = () => new URL(import.meta.env.BASE_URL, window.location.origin).href;

export default function SignIn({onSignIn,onBack,initialError=''}){
 const [mode,setMode]=useState('signup');
 const [name,setName]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState('');
 const [showPassword,setShowPassword]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(initialError),[notice,setNotice]=useState('');
 function switchMode(next){setMode(next);setPassword('');setConfirmation('');setError('');setNotice('')}
 async function submit(event){
  event.preventDefault();setError('');setNotice('');setBusy(true);
  try{
   if(mode==='signup'){
    setNotice(await register({name,email,password,confirmation,redirectTo:verificationRedirectTo()}));
    setPassword('');setConfirmation('');
   }else{
    const session=await login({email,password});
    setPassword('');onSignIn?.(session);
   }
  }catch(problem){setError(problem.message)}
  finally{setBusy(false)}
 }
 async function resend(){
  setBusy(true);setError('');setNotice('');
  try{setNotice(await resendVerification({email,redirectTo:verificationRedirectTo()}))}
  catch(problem){setError(problem.message)}
  finally{setBusy(false)}
 }
 return <div className="phone-shell demo-auth"><header className="welcome-header"><span className="brand">OneThing</span><button type="button" onClick={onBack}>Back</button></header><main className="demo-auth-body"><h1>{mode==='login'?<>Welcome <em>back.</em></>:<>Start your <em>journey.</em></>}</h1><div className="demo-auth-tabs" role="group" aria-label="Account options"><button type="button" aria-pressed={mode==='signup'} onClick={()=>switchMode('signup')}>Sign up</button><button type="button" aria-pressed={mode==='login'} onClick={()=>switchMode('login')}>Log in</button></div><form onSubmit={submit}>{mode==='signup'&&<label>Name<input value={name} onChange={e=>setName(e.target.value)} autoComplete="name" placeholder="Your name" required maxLength={80}/></label>}<label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" placeholder="you@example.com" required maxLength={254}/></label><label>Password<span className="auth-password-row"><input type={showPassword?'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} autoComplete={mode==='signup'?'new-password':'current-password'} placeholder="Your password" required minLength={mode==='signup'?8:1} maxLength={128}/><button type="button" onClick={()=>setShowPassword(v=>!v)} aria-label={showPassword?'Hide password':'Show password'}>{showPassword?<EyeOff size={17}/>:<Eye size={17}/>}</button></span></label>{mode==='signup'&&<label>Confirm password<input type={showPassword?'text':'password'} value={confirmation} onChange={e=>setConfirmation(e.target.value)} autoComplete="new-password" placeholder="Repeat password" required minLength={8} maxLength={128}/></label>}{error&&<p className="auth-feedback error" role="alert">{error}</p>}{notice&&<p className="auth-feedback" role="status">{notice}</p>}<button className="primary wide" type="submit" disabled={busy||!authConfigured}>{busy?'Please wait…':mode==='login'?'Log in':'Create account'}<ArrowRight size={18}/></button>{authConfigured&&email.trim()&&<button className="auth-resend" type="button" disabled={busy} onClick={resend}>Resend verification email</button>}{authConfigurationError&&<p className="auth-feedback error" role="alert">{authConfigurationError}</p>}</form></main></div>
}
