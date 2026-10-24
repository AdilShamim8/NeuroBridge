/**
 * Number contextualisation for the dyscalculia profile.
 *
 * Mirrors the Python pipeline's NumberContextualiser: exact fraction contexts
 * for percentages ("19% (19 in every 50)") and real-world magnitude
 * comparisons for currency amounts, instead of approximations and
 * placeholders.
 */

const PERCENT_RE = /(\d+(?:\.\d+)?)%/g;
const CURRENCY_RE = /(\$|EUR\s?|GBP\s?)(\d[\d,]*(?:\.\d+)?)(k|m|b| million| billion)?/gi;

/** Largest denominator used when converting a percentage to a fraction. */
const MAX_DENOMINATOR = 20;

/**
 * Reduce a numerator/denominator pair to lowest terms.
 */
function reduceFraction(numerator: number, denominator: number): [number, number] {
  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const divisor = gcd(numerator, denominator) || 1;
  return [numerator / divisor, denominator / divisor];
}

/**
 * Find the closest fraction with denominator <= maxDenominator to the given
 * ratio (0..1), mirroring fractions.Fraction.limit_denominator closely enough
 * for percentage annotation.
 */
function limitDenominator(ratio: number, maxDenominator: number): [number, number] {
  let bestNumerator = 0;
  let bestDenominator = 1;
  let bestError = Number.POSITIVE_INFINITY;
  for (let denominator = 1; denominator <= maxDenominator; denominator += 1) {
    const numerator = Math.round(ratio * denominator);
    const error = Math.abs(ratio - numerator / denominator);
    if (error < bestError - 1e-12) {
      bestNumerator = numerator;
      bestDenominator = denominator;
      bestError = error;
    }
  }
  return reduceFraction(bestNumerator, bestDenominator);
}

function percentContext(percent: number): string {
  if (percent === 10) return "1 in every 10";
  if (percent === 25) return "1 in 4";
  if (percent === 50) return "about half";
  if (percent === 75) return "3 in 4";
  if (percent === 1) return "1 in 100";
  const [numerator, denominator] = limitDenominator(percent / 100, MAX_DENOMINATOR);
  if (numerator === 1) return `1 in every ${denominator}`;
  if (numerator === 0) return "less than 1 in every 20";
  return `${numerator} in every ${denominator}`;
}

/** Dollar magnitude comparisons, mirroring the Python _DOLLAR_CONTEXTS table. */
const DOLLAR_CONTEXTS: { upTo: number; label: string }[] = [
  { upTo: 10, label: "roughly the cost of a lunch" },
  { upTo: 50, label: "roughly the cost of a restaurant dinner" },
  { upTo: 150, label: "roughly the cost of a weekly grocery shop" },
  { upTo: 500, label: "roughly the cost of a budget laptop" },
  { upTo: 2000, label: "roughly the cost of a used car repair" },
  { upTo: 10000, label: "roughly the cost of a used car" },
  { upTo: 100000, label: "roughly the cost of a new car" },
  { upTo: Number.POSITIVE_INFINITY, label: "roughly the cost of a house in many cities" }
];

function currencyContext(value: number): string {
  for (const tier of DOLLAR_CONTEXTS) {
    if (value <= tier.upTo) {
      return tier.label;
    }
  }
  return "a large amount";
}

function parseScaled(value: string, suffix?: string): number | null {
  const cleaned = value.replace(/,/g, "");
  const numeric = Number(cleaned);
  if (Number.isNaN(numeric)) {
    return null;
  }
  switch (suffix) {
    case "k":
      return numeric * 1_000;
    case "m":
      return numeric * 1_000_000;
    case "b":
      return numeric * 1_000_000_000;
    case " million":
      return numeric * 1_000_000;
    case " billion":
      return numeric * 1_000_000_000;
    default:
      return numeric;
  }
}

export function contextualizeNumbers(text: string): string {
  const withPercentContext = text.replace(PERCENT_RE, (_match, value) => {
    const numeric = Number(value);
    if (Number.isNaN(numeric)) {
      return `${value}%`;
    }
    return `${value}% (${percentContext(numeric)})`;
  });

  return withPercentContext.replace(
    CURRENCY_RE,
    (_match, symbol: string, value: string, suffix?: string) => {
      const amount = parseScaled(value, suffix);
      if (amount === null) {
        return `${symbol}${value}${suffix ?? ""}`;
      }
      return `${symbol}${value}${suffix ?? ""} (${currencyContext(amount)})`;
    }
  );
}
