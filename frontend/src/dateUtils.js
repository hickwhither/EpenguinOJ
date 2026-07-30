function parseDate(dateString) {
  if (!dateString) return null;
  if (dateString.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateString)) {
    return new Date(dateString);
  }
  return new Date(dateString + 'Z');
}

export function formatDate(dateString) {
  if (!dateString) return '';
  const date = parseDate(dateString);
  if (!date || isNaN(date.getTime())) return dateString;
  return date.toLocaleString(undefined, {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    day: '2-digit', month: '2-digit', year: 'numeric',
  });
}

export function formatDateWithLink(dateString) {
  if (!dateString) return { text: '', link: '' };
  const date = parseDate(dateString);
  if (!date || isNaN(date.getTime())) return { text: dateString, link: '' };
  const text = formatDate(dateString);
  const iso = date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const link = `https://www.timeanddate.com/worldclock/fixedtime.html?iso=${iso}`;
  return { text, link };
}
