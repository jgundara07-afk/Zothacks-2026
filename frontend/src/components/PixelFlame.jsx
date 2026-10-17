import React,{useEffect,useState} from 'react';

// A pixel-art flame for the intro. Frames are generated once (seeded, so they're the same every load) and cycled.
const W=13,H=18,FRAMES=8;
const COLORS={1:'#4a0d08',2:'#8a1e14',3:'#c8381c',4:'#ec6a20',5:'#f6a83a',6:'#fde08a',7:'#fff6dc'};

function seeded(seed){let s=seed;return()=>{s=(s*16807)%2147483647;return s/2147483647}}

function makeFrame(f){
 const rand=seeded(97+f*31),cells=[];
 for(let y=0;y<H;y++){
  const t=y/(H-1);                                   // 0 at the tip, 1 at the base
  const width=(W/2)*Math.sin(Math.min(1,t*1.15)*Math.PI*.62)*(0.82+rand()*.3);
  const sway=Math.sin(f*.9+y*.55)*(1-t)*1.6;
  for(let x=0;x<W;x++){
   const d=Math.abs(x-(W-1)/2-sway);
   if(d>width||(t<.12&&rand()<.55))continue;
   const heat=(1-d/Math.max(width,.01))*.65+t*.55+rand()*.12; // hotter toward the centre and the base
   const level=heat>1.05?7:heat>.92?6:heat>.78?5:heat>.62?4:heat>.45?3:heat>.3?2:1;
   cells.push([x,y,level]);
  }
 }
 return cells;
}
const FRAME_CELLS=Array.from({length:FRAMES},(_,f)=>makeFrame(f));

export default function PixelFlame({className='',style}){
 const [frame,setFrame]=useState(0);
 useEffect(()=>{
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const id=setInterval(()=>setFrame(f=>(f+1)%FRAMES),95);
  return()=>clearInterval(id);
 },[]);
 return <svg className={'pixel-flame '+className} style={style} viewBox={`0 0 ${W} ${H}`} shapeRendering="crispEdges" aria-hidden="true">
  {FRAME_CELLS[frame].map(([x,y,l])=><rect key={`${x}-${y}`} x={x} y={y} width="1.02" height="1.02" fill={COLORS[l]}/>)}
 </svg>
}
