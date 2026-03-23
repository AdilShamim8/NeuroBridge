const PERCENT_RE = /(\d+(?:\.\d+)?)%/g;
const CURRENCY_RE = /(\$|EUR\s?|GBP\s?)(\d[\d,]*(?:\.\d+)?)/gi;

export function contextualizeNumbers(text: string): string {
  const withPercentContext = text.replace(PERCENT_RE, (_match, value) => {
    const numeric = Number(value);
    if (Number.isNaN(numeric)) {
      return `${value}%`;
    }
    const ratio = Math.max(1, Math.round(numeric / 10));
    return `${numeric}% (about ${ratio} in 10)`;
  });

  return withPercentContext.replace(CURRENCY_RE, (_match, symbol, value) => {
    return `${symbol}${value} (contextualized amount)`;
  });
}
