import React,{useEffect,useRef,useState} from 'react';
import {Flag,Check,Sparkles} from 'lucide-react';
import {climbPosition,crossedMilestone} from '../utils/climbMath';
const TRAIL='M42 179 Q94 161 90 143 T126 108 T149 48';
export default function Climb({progress,fromPoints=null}){
 const path=useRef(null),marker=useRef(null),traveled=useRef(null);
 const [moving,setMoving]=useState(false),[arrived,setArrived]=useState(false);
 const target=climbPosition(progress.points),from=climbPosition(fromPoints??0);
 const milestone=fromPoints!==null&&crossedMilestone(fromPoints,progress.points);
 useEffect(()=>{
  const line=path.current;if(!line)return;
  const length=line.getTotalLength(),reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let frame,start;
  function paint(fraction){const p=line.getPointAtLength(fraction*length);marker.current?.setAttribute('transform',`translate(${p.x} ${p.y})`);if(traveled.current){traveled.current.style.strokeDasharray=String(length);traveled.current.style.strokeDashoffset=String(length*(1-fraction))}}
  const begin=from.mountain===target.mountain?Math.min(from.fraction,target.fraction):0;
  paint(begin);setArrived(false);
  if(reduced||begin===target.fraction){paint(target.fraction);setMoving(false);setArrived(true);return}
  setMoving(true);
  function tick(time){if(start===undefined)start=time;const t=Math.min(1,(time-start)/1600),ease=1-(1-t)**3;paint(begin+(target.fraction-begin)*ease);if(t<1)frame=requestAnimationFrame(tick);else{setMoving(false);setArrived(true)}}
  frame=requestAnimationFrame(tick);
  return()=>cancelAnimationFrame(frame);
 },[progress.points,fromPoints]);
 return <section className={`climb animated-climb ${arrived&&milestone?'milestone-arrived':''}`}><div className="section-heading"><h2>Your little climb</h2><span className="mountain-number">Mountain {target.mountain}<Flag size={15}/></span></div><svg className="mountain" viewBox="0 0 260 200" role="img" aria-label={`${progress.points} points, level ${target.level}, ${Math.round(target.fraction*100)} percent up mountain ${target.mountain}`}><path d="M0 180L63 87L99 124L149 37L260 180" fill="#dde5d2"/><path d="M149 37L126 77L146 69L163 83L175 75Z" fill="#faf9ef"/><path d="M0 180L63 87L113 160L140 180" fill="#bacda8"/><path ref={path} d={TRAIL} fill="none" stroke="#8d9e7c" strokeWidth="2" strokeDasharray="4 5"/><path ref={traveled} d={TRAIL} fill="none" stroke="#c5a35b" strokeWidth="3" strokeLinecap="round"/><path className={arrived&&milestone?'summit-flag celebrating':'summit-flag'} d="M149 38V16L171 21L149 29" fill="#d28862" stroke="#53664d"/><g ref={marker} transform="translate(42 179)" className={moving?'climb-marker walking':'climb-marker'}><circle className="climb-halo" r="15" fill="#e9c46b" opacity=".23"/><circle r="10" fill="#e9bd60" stroke="#fffdf3" strokeWidth="3"/><path d="M-4 0L-1 3L5-4" fill="none" stroke="#6a7f49" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></g>{arrived&&milestone&&<g className="summit-sparkles" aria-hidden="true"><path d="M185 31l3 7 8 3-8 3-3 8-3-8-7-3 7-3ZM113 13l2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#d9b154"/></g>}</svg><div className="climb-stats"><strong>{progress.points}<small> points</small></strong><span>Level {target.level}</span></div><div className="progress-track" role="progressbar" aria-label="Progress toward next hundred-point milestone" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress.points%100}><span style={{width:`${progress.points%100}%`}}/></div><small>{target.nextMilestone-progress.points} points to your next milestone</small>{milestone&&<div className="milestone-banner" role="status"><Sparkles size={18}/><span><strong>New milestone! Level {target.level}</strong><small>You passed {Math.floor(progress.points/100)*100} points. Keep climbing.</small></span><Check size={16}/></div>}</section>
}
