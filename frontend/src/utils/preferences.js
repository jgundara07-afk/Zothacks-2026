export function toggleSelection(value, choice, max = Infinity) {
  if (value.includes(choice)) return value.filter(item => item !== choice);
  if (value.length >= max) return value;
  return [...value, choice];
}
