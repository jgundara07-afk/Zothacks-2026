import React from 'react';

// The OneThing mark: a ring crossed by one tilted bar whose leading end turns red, with a stem dropped at the turn.
export default function Logo({size=30,className=''}){
 return <svg className={'brand-mark '+className} width={size} height={size} viewBox="64 64 352 352" aria-hidden="true" focusable="false">
  <path d="M87 270.2 L237 202 M226 207 L305.4 381.5" fill="none" stroke="var(--logo-ink)" strokeWidth="24"/>
  <path d="M237 202 L363.3 144.5" fill="none" stroke="var(--logo-red)" strokeWidth="24"/>
  {/* The ring is drawn last so it caps the bar and stem ends, as in the original mark. */}
  <circle cx="240" cy="240" r="156" fill="none" stroke="var(--logo-ink)" strokeWidth="24"/>
 </svg>;
}
