import React from 'react';

// Each interest becomes a region of the user's world.
const REGIONS={Design:'Design Highlands',Technology:'Signal Coast',Community:'Common Ground',Sustainability:'Greenwood Reach',Arts:'Lantern Bay'};

// The paper sheet that holds the page content: the user's own topographic world.
export default function World({name,interests,children}){
 return <section className="world">
  <div className="map-labels" aria-hidden="true">{interests.map(t=><span key={t}>{REGIONS[t]||t}</span>)}</div>
  <div className="world-bar">
   <div><span className="eyebrow">You are here</span><h2 className="world-title">{name}'s <em>world</em></h2></div>
   <ul className="world-regions" aria-label="Your regions">{interests.map(t=><li key={t}>{REGIONS[t]||t}</li>)}</ul>
   <span className="world-coords">33.6405° N · 117.8443° W</span>
  </div>
  {children}
 </section>
}
