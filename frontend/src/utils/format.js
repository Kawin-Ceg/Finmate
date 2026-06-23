export const CURRENCY_SYMBOLS = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  AUD: 'A$',
  CAD: 'C$',
  SGD: 'S$',
};

export function getCurrencySymbol(currencyCode = 'INR') {
  return CURRENCY_SYMBOLS[currencyCode] || CURRENCY_SYMBOLS.INR;
}

export function formatCurrency(value, currencyCode = 'INR', { maximumFractionDigits = 0 } = {}) {
  const symbol = getCurrencySymbol(currencyCode);
  if (value === null || value === undefined) return `${symbol}—`;
  return `${symbol}${Number(value).toLocaleString('en-IN', { maximumFractionDigits })}`;
}

export function formatSignedCurrency(value, type, currencyCode = 'INR') {
  const symbol = getCurrencySymbol(currencyCode);
  const formatted = Number(value).toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  return type === 'credit' ? `+${symbol}${formatted}` : `-${symbol}${formatted}`;
}

export function formatDateBySetting(dateStr, dateFormat = 'DD/MM/YYYY') {
  const d = new Date(dateStr + 'T00:00:00');
  if (Number.isNaN(d.getTime())) return dateStr;
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  const monthShort = d.toLocaleDateString('en-US', { month: 'short' });

  switch (dateFormat) {
    case 'MM/DD/YYYY':
      return `${month}/${day}/${year}`;
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`;
    case 'DD MMM YYYY':
      return `${day} ${monthShort} ${year}`;
    case 'DD/MM/YYYY':
    default:
      return `${day}/${month}/${year}`;
  }
}
