export function reorderByPriority(text: string): string {
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((item) => item.trim())
    .filter(Boolean);

  if (paragraphs.length <= 1) {
    return `Bottom line: ${paragraphs[0] || text}`.trim();
  }

  const [first, ...rest] = paragraphs;
  return [`Bottom line: ${first}`, ...rest].join("\n\n");
}
