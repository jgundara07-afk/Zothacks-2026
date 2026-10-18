// The five effort levels every quest is rated on. The backend stores the top level as "Challenging";
// players see it as "Locked-in". XP is the quest's points.
export const EFFORT_LEVELS = ['Lazy', 'Easy', 'Medium', 'Hard', 'Locked-in'];

export const effortLabel = difficulty => (difficulty === 'Challenging' ? 'Locked-in' : difficulty || 'Easy');
export const effortRank = difficulty => Math.max(0, EFFORT_LEVELS.indexOf(effortLabel(difficulty))) + 1; // 1–5

// A single quest with several steps, split so each step shows its own effort and XP (the XP adds up to the quest's).
// Effort climbs toward the quest's own level; XP is weighted the same way.
export function stepBreakdown(quest) {
  const steps = quest?.steps || [];
  if (steps.length < 2) return steps.map(text => ({ text, effort: effortLabel(quest?.difficulty), xp: quest?.points || 0 }));
  const top = effortRank(quest.difficulty);
  const ranks = steps.map((_, i) => Math.max(1, Math.round(top - (steps.length - 1 - i) * (top >= 4 ? 1 : 0.5))));
  const total = ranks.reduce((a, b) => a + b, 0);
  let given = 0;
  return steps.map((text, i) => {
    const xp = i === steps.length - 1 ? (quest.points || 0) - given : Math.round(((quest.points || 0) * ranks[i]) / total / 5) * 5;
    given += xp;
    return { text, effort: EFFORT_LEVELS[ranks[i] - 1], xp };
  });
}
