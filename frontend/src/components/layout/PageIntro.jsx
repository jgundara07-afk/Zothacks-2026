import React from 'react';
import {Sprout} from 'lucide-react';

// The big headline + subtitle at the top of each page.
const COPY={
 'Discover':{title:<>Big possibilities.<br/>Little <em>first steps.</em></>,text:'A few good things, picked for the person you’re becoming.'},
 'Saved things':{title:<>Your someday,<br/><em>starts here.</em></>,text:'Good ideas worth coming back to. Pick one and take a little step.'},
 'Resume lab':{title:<>A little clarity.<br/><em>Your next chapter.</em></>,text:'Find practice opportunities for the skills you want to build.'},
 'My recap':{title:<>Your little steps.<br/><em>In full color.</em></>,text:'Your progress deserves a moment in the spotlight.'},
 'My progress':{title:<>Look how far<br/><em>you've climbed.</em></>,text:'Every small step counts. These ones are yours.'},
};

export default function PageIntro({page}){
 const copy=COPY[page]||COPY['My progress'];
 return <section className="page-intro">
  <div><div className="eyebrow">LESS SCROLLING. MORE BECOMING.</div><h1>{copy.title}</h1><p>{copy.text}</p></div>
  <div className="daily-note"><span className="tape"/><span className="handwritten">a reminder for today</span><p>Small steps are<br/>still steps<span>♡</span></p><div className="note-bottom">YOU'RE DOING JUST FINE <Sprout size={30}/></div></div>
 </section>
}
