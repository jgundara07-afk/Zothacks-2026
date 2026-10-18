import React,{useEffect,useState} from 'react';

// Quest-complete stamp: an oxblood wax seal presses onto the parchment, then the points count up.
// Reduced motion shows the finished seal and total at once.
const SEAL=Array.from({length:28},(_,i)=>{const a=i/28*Math.PI*2,r=50+Math.sin(i*2.3)*2.6+Math.cos(i*5.1)*1.8;return `${(60+r*Math.cos(a)).toFixed(1)},${(60+r*Math.sin(a)).toFixed(1)}`}).join(' ');

function useCountUp(target,delay=520,duration=900){
 const [value,setValue]=useState(0);
 useEffect(()=>{
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){setValue(target);return}
  let frame,start;setValue(0);
  const timer=setTimeout(()=>{frame=requestAnimationFrame(function tick(time){start??=time;const t=Math.min(1,(time-start)/duration);setValue(Math.round(target*(1-(1-t)**3)));if(t<1)frame=requestAnimationFrame(tick)})},delay);
  return()=>{clearTimeout(timer);cancelAnimationFrame(frame)};
 },[target]);
 return value;
}

export default function RewardSeal({points}){
 const shown=useCountUp(points);
 return <div className="reward-stamp">
  <div className="reward-seal" aria-hidden="true">
   <span className="seal-ripple"/>
   <svg viewBox="0 0 120 120"><defs><radialGradient id="seal-wax" cx="38%" cy="32%" r="75%"><stop offset="0" stopColor="#b8443a"/><stop offset=".55" stopColor="#8a2620"/><stop offset="1" stopColor="#4d130f"/></radialGradient></defs><polygon points={SEAL} fill="url(#seal-wax)"/><circle cx="60" cy="60" r="37" className="seal-rim"/><circle cx="60" cy="60" r="31" className="seal-rim inner"/><path d="M43 62 55 74 79 47" className="seal-check"/></svg>
   <span className="seal-sparks">{Array.from({length:10},(_,i)=><i key={i} style={{'--i':i}}/>)}</span>
  </div>
  <p className="sr-only">{points} points earned</p>
  <div className="reward-points" aria-hidden="true">+{shown}<span>points</span></div>
 </div>;
}
