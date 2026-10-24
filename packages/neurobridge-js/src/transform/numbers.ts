/**
 * Number contextualisation for the dyscalculia profile.
 *
 * Faithful port of the Python pipeline's NumberContextualiser: exact fraction
 * contexts for percentages ("19% (19 in every 50)"), real-world magnitude
 * comparisons for currency and large counts, duration ranges, data sizes,
 * and very small decimals. Original values are always kept; only context is
 * appended, and matches already followed by a parenthetical are skipped so
 * context is never stacked.
 */

const DURATION_RANGE_RE = /(?<!\w)(\d+)\s*-\s*(\d+)\s*(years?|months?|weeks?|days?)(?!\w)/gi;
const DATA_SIZE_RE = /(?<!\w)(\d+(?:\.\d+)?)\s*(mb|gb|tb)(?!\w)/gi;
const PERCENT_RE = /(?<!\w)(\d+(?:\.\d+)?)%(?!\w)/g;
const CURRENCY_RE =
  /(?<!\w)([$£€]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|b|million|billion|trillion))?)(?!\w)/gi;
const LARGE_NUMBER_RE =
  /(?<!\()\b(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?\s?(?:million|billion|trillion))\b/gi;
const SMALL_DECIMAL_RE = /(?<!\w)(0\.\d+)(?!\w)/g;

/** Largest denominator used when converting a percentage to a fraction. */
const MAX_DENOMINATOR = 20;

const TIME_CONTEXTS: Record<string, string> = {
  days: "a short planning cycle",
  weeks: "a typical project sprint",
  months: "a full quarter of work",
  years: "a long-term planning window",
};

const DATA_CONTEXTS: Record<string, string> = {
  mb: "roughly a few high-resolution photos",
  gb: "roughly a short HD video",
  tb: "roughly a large enterprise backup",
};

const DOLLAR_CONTEXTS: [number, string][] = [
  [50, "roughly the cost of a weekly grocery run"],
  [200, "roughly the cost of a utility bill"],
  [1000, "roughly the cost of a budget laptop"],
  [10000, "roughly the cost of a used car"],
  [100000, "roughly the cost of a house deposit"],
  [1000000, "roughly the annual salary of 20 average workers"],
  [10000000, "roughly the annual salary of 200 average workers"],
  [100000000, "roughly the budget of a small city department"]
];

const PEOPLE_CONTEXTS: [number, string][] = [
  [1000, "about the size of a small school"],
  [10000, "about the size of a town neighborhood"],
  [100000, "about the size of a medium town"],
  [1000000, "about the population of a large city district"],
  [5000000, "about the population of a large metro area"],
  [10000000, "about the population of a major world city"]
];

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
  if (numerator === 0) {
    // Below 1/20 the denominator cap rounds to zero ("0 in every 1"), which
    // is mathematically false. State the bound instead.
    return "less than 1 in every 20";
  }
  return `${numerator} in every ${denominator}`;
}

/** Parse a scaled number token like "$1.2 million" or "3,400k". */
export function parseScaledNumber(token: string): number | null {
  let cleaned = token
    .toLowerCase()
    .replace("$", "")
    .replace("£", "")
    .replace("€", "")
    .replace(/,/g, "")
    .trim();
  let multiplier = 1;
  const scaled: [string, number][] = [
    ["k", 1_000],
    ["m", 1_000_000],
    ["b", 1_000_000_000],
    [" million", 1_000_000],
    [" billion", 1_000_000_000],
    [" trillion", 1_000_000_000_000]
  ];
  for (const [suffix, factor] of scaled) {
    if (cleaned.endsWith(suffix)) {
      multiplier = factor;
      cleaned = cleaned.slice(0, -suffix.length);
      break;
    }
  }
  const value = Number(cleaned) * multiplier;
  return Number.isFinite(value) && cleaned.trim() !== "" ? value : null;
}

/** bisect_left over context thresholds: first index with threshold >= value. */
function lookupContext(value: number, contexts: [number, string][]): string {
  for (let index = 0; index < contexts.length; index += 1) {
    if (contexts[index][0] >= value) {
      return contexts[index][1];
    }
  }
  return contexts[contexts.length - 1][1];
}

/**
 * Replace only matches that are not already followed by a parenthetical
 * context. The replacer receives (match, ...groups, offset, fullText).
 */
function replaceWithContext(
  text: string,
  pattern: RegExp,
  annotate: (match: string, groups: string[], offset: number, fullText: string) => string
): string {
  return text.replace(pattern, (match, ...rest) => {
    const offset = rest[rest.length - 2] as number;
    const fullText = rest[rest.length - 1] as string;
    const groups = rest.slice(0, -2).map((group) => String(group ?? ""));
    const suffix = fullText.slice(offset + match.length).replace(/^\s+/, "");
    if (suffix.startsWith("(")) {
      return match;
    }
    return annotate(match, groups, offset, fullText);
  });
}

/**
 * Contextualise every number form the Python pipeline covers, in the same
 * order: duration ranges, data sizes, percentages, currency, large counts,
 * and very small decimals.
 */
export function contextualizeNumbers(text: string): string {
  let output = replaceWithContext(text, DURATION_RANGE_RE, (match, groups) => {
    const start = Number(groups[0]);
    const end = Number(groups[1]);
    const unit = groups[2].toLowerCase();
    const unitKey = unit.replace(/s?$/, "s");
    const context = TIME_CONTEXTS[unitKey] ?? "a meaningful time window";
    return `${start}-${end} ${unit} (${context})`;
  });

  output = replaceWithContext(output, DATA_SIZE_RE, (match, groups) => {
    const amount = groups[0];
    const unit = groups[1].toLowerCase();
    const context = DATA_CONTEXTS[unit] ?? "a common storage amount";
    return `${amount} ${unit.toUpperCase()} (${context})`;
  });

  output = replaceWithContext(output, PERCENT_RE, (match, groups) => {
    const value = Number(groups[0]);
    if (!Number.isFinite(value)) {
      return match;
    }
    return `${match} (${percentContext(value)})`;
  });

  output = replaceWithContext(output, CURRENCY_RE, (match) => {
    const value = parseScaledNumber(match);
    if (value === null) {
      return match;
    }
    return `${match} (${lookupContext(value, DOLLAR_CONTEXTS)})`;
  });

  output = replaceWithContext(output, LARGE_NUMBER_RE, (match) => {
    const value = parseScaledNumber(match);
    if (value === null || value < 1000) {
      return match;
    }
    return `${match} (${lookupContext(value, PEOPLE_CONTEXTS)})`;
  });

  output = replaceWithContext(output, SMALL_DECIMAL_RE, (match, groups) => {
    const token = groups[0];
    const value = Number(token);
    if (!Number.isFinite(value) || value >= 0.1) {
      return token;
    }
    const denominator = value > 0 ? Math.max(10, Math.round(1 / value)) : 1000;
    return `${token} (a very small amount - about 1 in every ${denominator.toLocaleString("en-US")})`;
  });

  return output;
}
