import {Compass,Bookmark,Mountain,Pencil,Sparkles,Code2,Leaf,Feather} from 'lucide-react';

// Sidebar pages, in order. The name doubles as the page id used throughout the app.
export const NAV_ITEMS=[['Discover',Compass],['Saved things',Bookmark],['My progress',Mountain],['Resume lab',Pencil],['My recap',Sparkles]];

// Choices the backend accepts for a profile (see POST /profiles in backend/routes/profile.py).
export const GOALS=['Explore my interests','Build my skills','Make an impact'];
export const INTERESTS=['Design','Technology','Community','Sustainability','Arts'];
export const SKILLS=['Writing','Coding','Research','Design'];

// Daily check-in options: [value sent to the API, label shown on the button].
export const MOODS=[['Low','☁ Low energy'],['Okay','◒ Doing okay'],['Good','☀ Feeling good']];
export const EFFORTS=[['small','A small step · 2 min'],['big','Something bigger · 10–20 min']];

// Feed filters. The first entry of each list means "no filter".
export const TOPIC_FILTERS=['All opportunities','Design','Technology','Community','Sustainability'];
export const DIFFICULTIES=['Any','Lazy','Easy','Hard','Challenging'];
export const MODES=['Anywhere','Local','Online'];
export const GOAL_FILTERS=['Any goal',...GOALS];
export const SKILL_FILTERS=['Any skill','Coding','Design','Research','Writing'];
export const DEFAULT_FILTERS={topic:'All opportunities',difficulty:'Any',source:'All sources',mode:'Anywhere',goal:'Any goal',skill:'Any skill',gapSkills:[]};

// Card icons by opportunity id; anything not listed gets a sparkle.
export const OPPORTUNITY_ICONS={design:Pencil,code:Code2,green:Leaf,story:Feather};
export const DEFAULT_ICON=Sparkles;
