// Five quest categories, each with its own card color (see .quest-card.cat-* in styles/theme.css).
export const CATEGORIES = {
 career: 'Career',       // internships, jobs, networking
 learn: 'Learn',         // courses, classes, certifications, talks
 build: 'Build',         // hands-on technical courses, projects, hackathons, simulations
 community: 'Community', // clubs and campus or local events
 wellbeing: 'Wellbeing', // trails, parks, sports, general wellbeing tasks
};

const TECHNICAL = /code|coding|program|python|java|javascript|sql|software|web|app|api|cloud|data|machine learning|\bai\b|llm|devops|database|react|unity|engineer|develop|build|hack|robot|cyber/i;

export function categoryFor(o) {
 const kind = (o.kind || '').toLowerCase();
 const text = `${o.title || ''} ${(o.topics || []).join(' ')}`;
 if (o.recommendation_type === 'neutral' || /trail|park|sports|general task|hike/.test(kind)) return 'wellbeing';
 if (/internship|job|networking/.test(kind) || /\bintern(ship)?\b|career fair|recruit/i.test(o.title || '')) return 'career';
 if (/club|campus event|local event|initiative/.test(kind)) return 'community';
 if (/build challenge|creative project|simulation|project/.test(kind) || /hackathon/i.test(text)) return 'build';
 if (/course|class|certification/.test(kind)) return TECHNICAL.test(text) ? 'build' : 'learn';
 return 'learn';
}
