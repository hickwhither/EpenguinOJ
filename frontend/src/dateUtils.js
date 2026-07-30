function parseDate(value) {
  if (value == null) return null;
  if (typeof value === 'number') return new Date(value * 1000);
  if (value.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(value)) {
    return new Date(value);
  }
  return new Date(value + 'Z');
}

export function formatDate(value) {
  if (value == null) return '';
  const date = parseDate(value);
  if (!date || isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    day: '2-digit', month: '2-digit', year: 'numeric',
  });
}

export function formatDateWithLink(value) {
  if (value == null) return { text: '', link: '' };
  const date = parseDate(value);
  if (!date || isNaN(date.getTime())) return { text: String(value), link: '' };
  const text = formatDate(value);
  const iso = date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const link = `https://www.timeanddate.com/worldclock/fixedtime.html?iso=${iso}`;
  return { text, link };
}
