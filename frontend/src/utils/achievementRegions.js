export const REGIONS=[['foundations','The First Range'],['ascent','The Ascent'],['climb','The Crucible'],['explorer','The Far Horizons'],['strategist','The Strategist’s Spires'],['backlog','The Forgotten Trails'],['community','The Kindred Peaks'],['wellness','The Restful Highlands'],['hustle','The Readiness Ridge'],['milestones','The Storykeeper’s Range']];
// Every achievement is named for its mountain (backend/achievements.py and achievement_catalog.json).
export function mountainName(badge){return badge.name;}
export function badgeSeed(id){return [...id].reduce((value,char)=>(value*31+char.charCodeAt(0))>>>0,7);}
