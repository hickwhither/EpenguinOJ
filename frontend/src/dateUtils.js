export function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString(undefined, {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    day: '2-digit', month: '2-digit', year: 'numeric',
  });
}

export function formatDateWithLink(dateString) {
  if (!dateString) return { text: '', link: '' };
  const date = new Date(dateString);
  const text = formatDate(dateString);
  const iso = date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const link = `https://www.timeanddate.com/worldclock/fixedtime.html?iso=${iso}`;
  return { text, link };
}
