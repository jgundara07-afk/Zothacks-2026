import React from 'react';
import {OPPORTUNITY_ICONS,DEFAULT_ICON} from '../constants';

// A quest's hero photograph with the live analog layer (grain, scanlines) over its baked-in grade.
// Without a src it falls back to tinted halftone art with an icon.
export default function Print({src,color,icon,osd,children}){
 const Icon=icon||DEFAULT_ICON;
 return <div className={'print '+(color||'')}>
  {src?<img src={src} alt="" loading="lazy"/>:<div className="print-fallback" aria-hidden="true"><Icon size={56} strokeWidth={1}/></div>}
  <div className="grain" aria-hidden="true"/>
  {osd&&<div className="osd" aria-hidden="true"><span className="rec">REC</span><span>{osd}</span></div>}
  {children}
 </div>
}
