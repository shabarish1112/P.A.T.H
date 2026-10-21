export function formatMoney(paise) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format((paise || 0) / 100);
}

export function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value || 0);
}

export function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}
