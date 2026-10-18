const allowedDomains = new Set([
  'gmail.com', 'outlook.com', 'hotmail.com', 'live.com', 'yahoo.com',
  'icloud.com', 'me.com', 'mac.com', 'proton.me', 'protonmail.com', 'uci.edu',
]);
export const acceptedProviders = 'Gmail, Outlook/Hotmail/Live, Yahoo, iCloud, Proton, or UC Irvine';
export function normalizeEmail(value) {
  const trimmed = typeof value === 'string' ? value.trim() : '';
  const match = /^([A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)$/.exec(trimmed);
  if (!match || trimmed.length > 254 || match[1].length > 64 || match[1].startsWith('.') || match[1].endsWith('.') || match[1].includes('..') || match[2].split('.').some(label => label.startsWith('-') || label.endsWith('-'))) {
    throw new Error('Enter a valid email address.');
  }
  const domain = match[2].toLowerCase();
  if (!allowedDomains.has(domain)) throw new Error(`Use a ${acceptedProviders} email address.`);
  return `${match[1]}@${domain}`;
}
