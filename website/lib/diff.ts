export type DiffToken = {
  value: string;
  type: "equal" | "added" | "removed";
};

export type DiffSummary = {
  wordsSimplified: number;
  chunksCreated: number;
  urgencySoftened: number;
};

const URGENCY_RE = /\b(asap|immediately|critical|urgent|must|now)\b/gi;

function tokenize(text: string): string[] {
  return text.trim().split(/\s+/).filter(Boolean);
}

function lcsMatrix(a: string[], b: string[]): number[][] {
  const matrix: number[][] = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      if (a[i] === b[j]) {
        matrix[i][j] = matrix[i + 1][j + 1] + 1;
      } else {
        matrix[i][j] = Math.max(matrix[i + 1][j], matrix[i][j + 1]);
      }
    }
  }
  return matrix;
}

export function wordDiff(original: string, adapted: string): DiffToken[] {
  const left = tokenize(original);
  const right = tokenize(adapted);
  const matrix = lcsMatrix(left, right);

  let i = 0;
  let j = 0;
  const diff: DiffToken[] = [];

  while (i < left.length && j < right.length) {
    if (left[i] === right[j]) {
      diff.push({ value: left[i], type: "equal" });
      i += 1;
      j += 1;
    } else if (matrix[i + 1][j] >= matrix[i][j + 1]) {
      diff.push({ value: left[i], type: "removed" });
      i += 1;
    } else {
      diff.push({ value: right[j], type: "added" });
      j += 1;
    }
  }

  while (i < left.length) {
    diff.push({ value: left[i], type: "removed" });
    i += 1;
  }
  while (j < right.length) {
    diff.push({ value: right[j], type: "added" });
    j += 1;
  }

  return diff;
}

export function summarizeChanges(original: string, adapted: string): DiffSummary {
  const originalWords = tokenize(original);
  const adaptedWords = tokenize(adapted);
  const wordsSimplified = Math.max(0, originalWords.length - adaptedWords.length);
  const chunksCreated = Math.max(1, adapted.split(/\n\n+/).filter((part) => part.trim()).length);

  const originalUrgency = original.match(URGENCY_RE)?.length ?? 0;
  const adaptedUrgency = adapted.match(URGENCY_RE)?.length ?? 0;
  const urgencySoftened = Math.max(0, originalUrgency - adaptedUrgency);

  return {
    wordsSimplified,
    chunksCreated,
    urgencySoftened
  };
}
