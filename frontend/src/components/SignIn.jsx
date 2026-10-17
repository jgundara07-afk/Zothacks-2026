import React from 'react';
import {ArrowRight,Mail,Check} from 'lucide-react';
import {OPENING_HALFTONE} from '../constants';

// Opening screen. Composition follows design/references/iris-halftone-signin-reference.png:
// a ghosted photograph above a crisp panel, with a halftone of the same photo as texture.
export default function SignIn({onSignIn}){
 return <div className="phone-shell signin-shell"><header className="welcome-header"><span className="brand">one thing<span>✳</span></span><span className="signin-demo-label">ZotHacks demo</span></header>
  <main className="signin-content">
   <div className="signin-photo" aria-hidden="true"><span>One thing / 001<br/>33.6405° N · 117.8443° W</span></div>
   <div className="signin-panel">
    <img className="signin-halftone" src={OPENING_HALFTONE} alt="" aria-hidden="true"/>
    <div className="signin-eyebrow"><span>Your next chapter starts small</span></div>
    <h1>A little less scroll.<br/>A little more <em>you.</em></h1>
    <p className="signin-copy">Welcome back. Find something worth your time, take a baby step, and watch your progress grow.</p>
    <form onSubmit={e=>{e.preventDefault();onSignIn()}}><label htmlFor="demo-account">Your demo account</label><div className="signin-account"><Mail size={18}/><input id="demo-account" type="email" value="alex@example.com" readOnly aria-describedby="signin-notice"/><Check size={16}/></div><p id="signin-notice" className="signin-notice">You're entering Alex's shared fictional profile. No password or private account is created.</p><button className="primary wide" type="submit">Sign in to demo<ArrowRight size={18}/></button></form>
    <p className="signin-footer">1% every day. One thing at a time.</p>
   </div>
  </main></div>
}
