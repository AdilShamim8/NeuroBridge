/**
 * Region protection shared by the transform modules.
 *
 * Mirrors the Python pipeline's `_protect_regions`: fenced code blocks and
 * numbered list blocks must never be rewritten, re-toned, or re-chunked,
 * because transforming code or list markup corrupts it. Modules receive the
 * text split into segments, each flagged as transformable or protected.
 */

export interface TextRegion {
  text: string;
  protected: boolean;
}

const FENCED_BLOCK_RE = /```[\s\S]*?```/g;
const NUMBERED_LIST_BLOCK_RE = /(?:^|\n)(?:[ \t]*\d+\.[ \t].+(?:\n|$))+/g;

/** Split text into transformable and protected regions. */
export function protectRegions(text: string): TextRegion[] {
  const spans: Array<[number, number]> = [];
  for (const pattern of [FENCED_BLOCK_RE, NUMBERED_LIST_BLOCK_RE]) {
    pattern.lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      spans.push([match.index, match.index + match[0].length]);
    }
  }
  if (!spans.length) {
    return [{ text, protected: false }];
  }

  spans.sort((a, b) => a[0] - b[0]);
  const merged: Array<[number, number]> = [];
  for (const span of spans) {
    const last = merged[merged.length - 1];
    if (!last || span[0] > last[1]) {
      merged.push(span);
    } else {
      last[1] = Math.max(last[1], span[1]);
    }
  }

  const regions: TextRegion[] = [];
  let cursor = 0;
  for (const [start, end] of merged) {
    if (start > cursor) {
      regions.push({ text: text.slice(cursor, start), protected: false });
    }
    regions.push({ text: text.slice(start, end), protected: true });
    cursor = end;
  }
  if (cursor < text.length) {
    regions.push({ text: text.slice(cursor), protected: false });
  }
  return regions;
}

/**
 * Apply `transform` only to transformable regions and stitch the protected
 * regions back verbatim.
 */
export function mapUnprotectedRegions(
  text: string,
  transform: (region: string) => string
): string {
  return protectRegions(text)
    .map((region) => (region.protected ? region.text : transform(region.text)))
    .join("");
}
