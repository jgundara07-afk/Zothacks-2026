import React from 'react';

// The big headline + subtitle at the top of each page, on the dark frame.
const COPY={
 'Discover':{title:<>Big possibilities.<br/>Little <em>first steps.</em></>,text:'A few good things, picked for the person you’re becoming.'},
 'Saved things':{title:<>Your someday,<br/>starts <em>here.</em></>,text:'Good ideas worth coming back to. Pick one and take a little step.'},
 'Resume lab':{title:<>A little clarity.<br/>Your next <em>chapter.</em></>,text:'Find practice opportunities for the skills you want to build.'},
 'My recap':{title:<>Your little steps.<br/>In full <em>color.</em></>,text:'Your progress deserves a moment in the spotlight.'},
 'My progress':{title:<>Look how far<br/>you've <em>climbed.</em></>,text:'Every small step counts. These ones are yours.'},
};

export default function PageIntro({page}){
 const copy=COPY[page]||COPY['My progress'];
 return <section className="page-intro">
  <div><div className="eyebrow">Less scrolling. More becoming.</div><h1>{copy.title}</h1><p>{copy.text}</p></div>
  <div className="daily-note"><span className="handwritten">A reminder for today</span><p>Small steps are still <em>steps.</em></p><div className="note-bottom">You're doing just fine</div></div>
 </section>
}
