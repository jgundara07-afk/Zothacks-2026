import React from 'react';

// Hand-inked mountain glyphs in the style of the parchment map: a lit face, a hatched shadow face, an ink outline.
// The tallest peak sits under the summit flag at (149, 38); the climb trail runs over them.
const PEAKS=[[40,112,13],[105,112,22],[190,104,24],[70,142,17],[214,152,18],[125,152,13],[176,172,14],[149,70,28]];

function Peak({x,y,s}){
 const top=[x,y-s*1.15],left=[x-s*.8,y],right=[x+s*.8,y],foot=[x+s*.1,y];
 const hatch=[1,2,3,4,5].map(k=>{const t=k/6;return <line key={k} x1={top[0]+(right[0]-top[0])*t} y1={top[1]+(right[1]-top[1])*t} x2={foot[0]} y2={y}/>});
 return <g>
  <path d={`M${left} L${top} L${right} Z`} className="peak-lit"/>
  <path d={`M${top} L${right} L${foot} Z`} className="peak-shade"/>
  <g className="peak-hatch">{hatch}</g>
  <path d={`M${left} L${top} L${right}`} className="peak-ink"/>
 </g>
}

export default function FantasyPeaks(){
 return <g className="fantasy-peaks" aria-hidden="true">{PEAKS.map(([x,y,s])=><Peak key={`${x}-${y}`} x={x} y={y} s={s}/>)}</g>
}
