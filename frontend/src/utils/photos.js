// Hero photography. Every quest is matched to a romantic "scene"; each scene has one or more graded photos in
// frontend/public/photos/scenes/ (CC0, see CREDITS.json there). All photos share one AURA-style grade and grain,
// so the feed reads as a single body of work rather than a pile of stock.

export const SCENES = {
 cafe: ['cafe-real', 'cafe-1', 'cafe-2'],
 hike: ['hike-1', 'hike-2'],
 stream: ['stream-1'],
 garden: ['garden-1', 'garden-2'],
 code: ['code-1', 'code-2'],
 writing: ['writing-real', 'writing-1', 'writing-2'],
 library: ['library-1', 'library-2'],
 sketch: ['sketch-real', 'sketch-1', 'sketch-2'],
 friends: ['friends-1', 'friends-2'],
 evening: ['evening-1'],
 finance: ['finance-1', 'finance-2'],
 lab: ['garden-2'],
 maker: ['sketch-real', 'maker-1'],
 audio: ['audio-1', 'audio-2'],
 citynight: ['citynight-1', 'citynight-2'],
 window: ['window-1', 'window-2'],
 sports: ['sports-1', 'sports-2'],
 chess: ['chess-1'],
 journal: ['journal-1'],
 stage: ['stage-1'],
 train: ['train-1'],
 map: ['map-1', 'map-2'],
};

// First matching rule wins: [scene, words found in the quest's id, title or kind].
const RULES = [
 ['hike', /hike|trail/],
 ['stream', /creek|water|river/],
 ['cafe', /coffee|networking|mentor|ask a|alumni|co-builder|questions to ask|introduce your|shadow/],
 ['sports', /badminton|sport|rally/],
 ['garden', /compost|plant|green|reroot|garden|reuse|refill|repair|sustainab|climate|solar|energy/],
 ['audio', /audio|radio|podcast|fm\b|story sprint/],
 // Technical courses and roles go to the coding scenes before the generic library scene.
 ['code', /code|coding|python|java|javascript|sql|backend|frontend|web|api|cloud|html|developer|software|program|hack|machine|classifier|llm|\bai\b|react|pandas|database|unity|data|devops|kubernetes/],
 ['lab', /lab |lab-|biolog|science|biotech|sample log|biosketch|medical/],
 ['maker', /robot|rover|maker|cad|desk tool|hardware|sensor|delivery bot/],
 ['citynight', /security|phishing|privacy|suspicious|cyber/],
 ['finance', /financ|invest|budget|spreadsheet|portfolio lab/],
 ['chess', /debate|policy|strategy|product thinking|product sprint|product manager|simulation-product/],
 ['stage', /pitch|career fair|careers in|poster|launch/],
 ['sketch', /design|ux|figma|canvas|wayfinding|critique|interface|accessible ui|visual/],
 ['writing', /writing|writer|magazine|column|story|technical writing|lantern|communicat/],
 ['map', /transit|shuttle|bus|route|map|visualiz|wayfind/],
 ['journal', /focus|ritual|planning|productiv|notes/],
 ['friends', /club|picnic|circle|crew|neighbors|founder/],
 ['evening', /event|night|fair|tea/],
 ['library', /class|sql|course|certification|badge|research|library|interview|study/],
 ['window', /intern/],
 ['train', /.*/],
];

function hash(text) { let h = 0; for (const c of text) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h; }

export function sceneFor(opportunity) {
 const text = `${opportunity.id} ${opportunity.title} ${opportunity.kind}`.toLowerCase();
 return (RULES.find(([, pattern]) => pattern.test(text)) || RULES[RULES.length - 1])[0];
}

export function scenePhoto(scene, key = '') {
 const list = SCENES[scene] || SCENES.train;
 return `/photos/scenes/${list[hash(key) % list.length]}.jpg`;
}

// Hand-picked photos for specific quests (the user's real-photo shortlist, design/references/aura-real-photos).
const OVERRIDES = { network: 'cafe-real', 'sample-networking-backend': 'cafe-real', code: 'sketch-real', club: 'sketch-real', story: 'writing-real' };

export function photoFor(opportunity) {
 const fixed = OVERRIDES[opportunity.id];
 return fixed ? `/photos/scenes/${fixed}.jpg` : scenePhoto(sceneFor(opportunity), opportunity.id);
}

// Photo tiles for onboarding interests.
export const INTEREST_SCENES = {
 'Software Engineering': 'code', 'AI & Machine Learning': 'citynight', 'Web & App Development': 'code', 'Data Science': 'map',
 'Cybersecurity': 'citynight', 'Entrepreneurship & Startups': 'stage', 'Hackathons': 'evening', 'Career Development': 'window',
 'Networking & Mentorship': 'cafe', 'Leadership': 'chess', 'Personal Finance & Investing': 'finance',
 'Productivity & Personal Growth': 'journal', 'Design & UI/UX': 'sketch', 'Hike': 'hike', 'Sports': 'sports',
};

// For a list (the feed), rotate through each scene's photos in order so neighbouring cards from the same scene
// don't repeat a photo when the scene has more than one. Returns Map(id → src).
export function photosForList(list) {
 const seen = {}, out = new Map();
 for (const o of list) {
  if (OVERRIDES[o.id]) { out.set(o.id, `/photos/scenes/${OVERRIDES[o.id]}.jpg`); continue; }
  const scene = sceneFor(o), photos = SCENES[scene] || SCENES.train, n = seen[scene] = (seen[scene] ?? -1) + 1;
  out.set(o.id, `/photos/scenes/${photos[(hash(scene) + n) % photos.length]}.jpg`);
 }
 return out;
}
