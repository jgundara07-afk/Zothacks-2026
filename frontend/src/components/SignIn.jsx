import React,{useRef,useState} from 'react';
import {authConfigured,authConfigurationError} from '../auth';
import {startGoogleSignIn} from '../authFlow';
import Logo from './Logo';

const redirectToApp = () => new URL(import.meta.env.BASE_URL, window.location.origin).href;

export default function SignIn({onBack,initialError=''}){
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState(initialError);
 const requestInFlight=useRef(false);

 async function googleSignIn(){
  if(requestInFlight.current)return;
  requestInFlight.current=true;
  setBusy(true);
  setError('');
  try{await startGoogleSignIn({redirectTo:redirectToApp()})}
  catch(problem){setError(problem.message)}
  finally{requestInFlight.current=false;setBusy(false)}
 }

 return <div className="phone-shell demo-auth">
  <header className="welcome-header"><span className="brand-lockup"><Logo/><span className="brand">OneThing</span></span><button type="button" onClick={onBack}>Back</button></header>
  <main className="demo-auth-body auth-google-only">
   <h1>Start your <em>journey.</em></h1>
   <p className="auth-intro">Sign in or create an account with Google.</p>
   {error&&<p className="auth-feedback error" role="alert">{error}</p>}
   <button className="auth-google" type="button" disabled={busy||!authConfigured} onClick={googleSignIn}>
    <span className="auth-google-mark" aria-hidden="true">G</span>{busy?'Connecting…':'Continue with Google'}
   </button>
   {authConfigurationError&&<p className="auth-feedback error" role="alert">{authConfigurationError}</p>}
  </main>
 </div>;
}
