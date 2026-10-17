import React from 'react';
import {OPPORTUNITY_PHOTOS,OPPORTUNITY_ICONS,DEFAULT_ICON} from '../constants';

// A quest's hero image with the analog treatment (grade, grain, scanlines).
// Until a photo is added in constants.js it shows halftone terrain tinted by the card color.
export default function Print({id,color,osd,children}){
 const photo=OPPORTUNITY_PHOTOS[id];
 const Icon=OPPORTUNITY_ICONS[id]||DEFAULT_ICON;
 return <div className={'print '+(color||'')+(photo?.bw?' bw':'')}>
  {photo?<img src={photo.src} alt="" loading="lazy"/>:<div className="print-fallback" aria-hidden="true"><Icon size={56} strokeWidth={1}/></div>}
  <div className="grain" aria-hidden="true"/>
  {osd&&<div className="osd" aria-hidden="true"><span className="rec">REC</span><span>{osd}</span></div>}
  {children}
 </div>
}
