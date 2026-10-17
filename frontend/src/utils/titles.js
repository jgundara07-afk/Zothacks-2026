// Turn messy catalog titles into names you can read in one second, plus a subline for the rest.
// "2027 Quantitative Research - Markets - Summer Internship - Associate- United States" (JPMorgan Chase)
//   → title "Quantitative Research Summer Internship", subline "JPMorgan Chase · 2027"
// The original title is still shown in the detail sheet.

const KIND_LABELS = {
 'Online course': 'Course', 'Campus event': 'Event', 'Local event': 'Event', 'Job simulation': 'Simulation',
 'Creative project': 'Project', 'Build challenge': 'Challenge', 'Campus initiative': 'Initiative',
};
export const kindLabel = kind => KIND_LABELS[kind] || kind || 'Quest';

const ABBREVIATIONS = [[/\bEngr\b/g, 'Engineer'], [/\bMgr\b/g, 'Manager'], [/\bSr\b\.?/g, 'Senior'], [/\bJr\b\.?/g, 'Junior'], [/\bAssoc\b\.?/g, 'Associate']];
// Words that carry no meaning on a card.
const NOISE = /\b(19|20)\d{2}\b|\b'?\d{2}\s*\/\s*'?\d{2}\b|\bnew grad(uate)?( hiring)?\b|\bassociate\b|\bunited states\b|\bUS\b|\bUSA\b|\bremote\b|\bhybrid\b|\bfull[- ]time\b|\bpart[- ]time\b|\bstart\b|\bjoin our talent community\b|\b(BS|MS|PhD)(\/(BS|MS|PhD))*\b|\bin[- ]person\b|\bvirtual\b|\bqwik start\b/gi;
const PREFIX = /^(in[- ]person|virtual|online|hybrid|webinar|workshop series)\s*:\s*/i;
const SEASON = /\b(summer|fall|autumn|winter|spring)\b/i;
// Event-ish nouns help pick the segment that names the thing; "club" is left out so a host club never wins over the topic.
const EVENT_NOUN = /\b(workshop|session|sessions|talk|lecture|series|night|fair|panel|summit|showcase|clinic|meetup|hackathon|bootcamp|sprint)\b/i;
const KIND_NOUN = /\b(workshop|session|sessions|talk|lecture|series|night|fair|course|lab|club|circle|program|internship|intern|engineer|analyst|scientist|developer|designer|manager|specialist|researcher|writer|technician|consultant|assistant|coordinator|advisor|sprint|chat|meetup|hackathon|bootcamp|clinic|panel|summit|showcase)\b/i;

const clean = s => s.replace(/\u200b|\ufffd/g, '').replace(/\\\//g, '/').replace(/\s+/g, ' ').trim();
const titleCase = s => s.replace(/\b([a-z])([a-z]*)/g, (m, a, b) => (/^(of|and|for|to|the|in|on|at|a|an|with)$/.test(m) ? m : a.toUpperCase() + b));

// Split on " - ", " | ", ":", " — " and drop parentheses/brackets.
function segments(title) {
 return clean(title.replace(PREFIX, '')).replace(/\([^)]*\)|\[[^\]]*\]/g, ' ').split(/\s+[-–—|]\s*|\s*\|\s*|:\s*|\s+-|-\s+/).map(clean).filter(Boolean);
}

function strip(text, dropInternWords) {
 let s = text;
 for (const [pattern, word] of ABBREVIATIONS) s = s.replace(pattern, word);
 s = s.replace(/^([\w&/ ]+),\s*(\w+)$/, '$2 $1');                 // "Engineer, Mechanical" → "Mechanical Engineer"
 s = s.replace(NOISE, ' ').replace(/\b(summer|fall|autumn|winter|spring)\b/gi, ' ');
 if (dropInternWords) s = s.replace(/\b(project intern|internship|intern)\b/gi, ' ');
 return clean(s).replace(/\s+\d+$/, '').replace(/^[,/&\s]+|[,/&\s]+$/g, '');
}

// Long names get cut at a connecting word ("Migrating MySQL Using a ..." → "Migrating MySQL");
// "with/featuring" always ends the name so speakers drop off ("Acting Workshop with ..." → "Acting Workshop").
function shorten(text, max = 5) {
 const words = text.split(' ');
 const speaker = words.findIndex((w, i) => i >= 2 && /^(with|featuring|ft\.?|x)$/i.test(w));
 if (speaker > 0) return words.slice(0, speaker).join(' ');
 if (words.length <= max) return text;
 const cut = words.findIndex((w, i) => i >= 2 && /^(using|for|at|in|to|from|by|via|and)$/i.test(w));
 return words.slice(0, cut > 0 && cut <= max ? cut : max).join(' ');
}

export function simpleTitle(o) {
 const raw = o.title || '';
 const parts = segments(raw);
 if (o.kind === 'Internship') {
  const field = parts.map(p => strip(p, true)).find(p => p && !/^(markets|program|strategic student program)$/i.test(p)) || 'Student';
  const season = (raw.match(SEASON) || [])[1];
  return clean(`${titleCase(shorten(field, 4))} ${season ? titleCase(season.toLowerCase()) + ' ' : ''}Internship`).replace(/\s*\/\s*/g, ' & ');
 }
 const stripped = parts.map(p => strip(p, false)).filter(Boolean);
 // Prefer the segment that names the thing (workshop, engineer, course...), else the first one.
 const noun = /event/i.test(o.kind || '') ? EVENT_NOUN : KIND_NOUN;
 const named = stripped.length > 1 ? stripped.find(p => noun.test(p) && p.split(' ').length > 1) : null;
 const best = named || (stripped[0] && stripped[0].length < 4 && stripped[1] ? stripped[1] : stripped[0]) || clean(raw);
 return shorten(best).replace(/\s*\/\s*/g, ' & ');
}

export function subline(o) {
 const year = ((o.title || '').match(/\b(20\d{2})\b/) || [])[1];
 const org = (o.organization || '').replace(/\s*\(see course page.*$/i, '').replace(/\s*\(SCE\)$/, '').trim();
 const place = o.mode && o.mode !== 'Check source' ? o.mode : o.city || '';
 // A course's subtitle ("Advanced JavaScript 1: Objects, Loops, Hoisting") moves here so nothing is lost.
 const sub = /course/i.test(o.kind || '') && (o.title || '').includes(':') ? clean(o.title.split(':').slice(1).join(':')) : '';
 return [sub, org, place, year].filter(Boolean).join(' · ');
}

// A short description for cards: the first sentence or two, cut at a word boundary.
export function blurb(text = '', max = 150) {
 const t = clean(text);
 if (t.length <= max) return t;
 const sentences = t.match(/[^.!?]+[.!?]+/g) || [];
 let out = '';
 for (const s of sentences) { if ((out + s).length > max) break; out += s; }
 return out.trim() || t.slice(0, t.lastIndexOf(' ', max)) + '…';
}
