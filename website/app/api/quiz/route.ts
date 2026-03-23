import { NextRequest, NextResponse } from "next/server";

const profileMap = ["adhd", "autism", "dyslexia", "anxiety", "dyscalculia"] as const;

type ProfileId = (typeof profileMap)[number];

type QuizOption = {
  id: string;
  label: string;
  scores: Record<ProfileId, number>;
};

type QuizQuestion = {
  id: string;
  text: string;
  options: QuizOption[];
};

const QUESTIONS: QuizQuestion[] = [
  {
    id: "q1",
    text: "When reading AI output, what helps first?",
    options: [
      { id: "a", label: "A one-line summary before details", scores: { adhd: 3, autism: 0, dyslexia: 1, anxiety: 1, dyscalculia: 0 } },
      { id: "b", label: "Exact wording with concrete definitions", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 1, dyscalculia: 1 } },
      { id: "c", label: "Shorter lines and simpler sentence flow", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 1 } },
      { id: "d", label: "A gentler tone with less urgency", scores: { adhd: 0, autism: 1, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q2",
    text: "How do you prefer long task explanations?",
    options: [
      { id: "a", label: "Chunked into clearly ordered steps", scores: { adhd: 3, autism: 1, dyslexia: 1, anxiety: 0, dyscalculia: 1 } },
      { id: "b", label: "Literal and unambiguous all the way", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 1, dyscalculia: 1 } },
      { id: "c", label: "Plain, simple language with spacing", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Calm framing that avoids pressure", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 1 } }
    ]
  },
  {
    id: "q3",
    text: "Numbers are easiest when they are...",
    options: [
      { id: "a", label: "Connected to practical examples", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 0, dyscalculia: 3 } },
      { id: "b", label: "Concise with only key values", scores: { adhd: 2, autism: 1, dyslexia: 1, anxiety: 0, dyscalculia: 1 } },
      { id: "c", label: "Presented very literally and consistently", scores: { adhd: 0, autism: 2, dyslexia: 0, anxiety: 0, dyscalculia: 1 } },
      { id: "d", label: "Surrounded by reassurance and context", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 2, dyscalculia: 1 } }
    ]
  },
  {
    id: "q4",
    text: "When a response feels hard to process, why is that usually?",
    options: [
      { id: "a", label: "It hides the main point too deep", scores: { adhd: 3, autism: 1, dyslexia: 1, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "It uses vague language or idioms", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Sentences are dense and visually tiring", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "The tone feels urgent or alarming", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q5",
    text: "Which format helps you stay engaged?",
    options: [
      { id: "a", label: "Top-line answer, then bullets", scores: { adhd: 3, autism: 0, dyslexia: 1, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Exact terminology and explicit detail", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 1, dyscalculia: 1 } },
      { id: "c", label: "One idea per short sentence", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Supportive wording and lower intensity", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q6",
    text: "For task planning, what works best?",
    options: [
      { id: "a", label: "Priority order from most important to least", scores: { adhd: 3, autism: 1, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Rules and conditions made very explicit", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Smaller blocks with generous spacing", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "A calm tone that avoids pressure words", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q7",
    text: "How should AI handle uncertainty?",
    options: [
      { id: "a", label: "Give the answer first, caveats second", scores: { adhd: 2, autism: 1, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "State unknowns directly and literally", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Use straightforward wording with short lines", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Use reassuring language without alarm", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q8",
    text: "When examples are included, I prefer...",
    options: [
      { id: "a", label: "Short practical examples near each step", scores: { adhd: 2, autism: 1, dyslexia: 1, anxiety: 0, dyscalculia: 1 } },
      { id: "b", label: "Precise and literal examples", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 1 } },
      { id: "c", label: "Visual clarity over complexity", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Calm examples that avoid stress cues", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q9",
    text: "For deadlines and risk language, I prefer...",
    options: [
      { id: "a", label: "A brief summary, then constraints", scores: { adhd: 2, autism: 1, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Direct, exact statements", scores: { adhd: 0, autism: 2, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Very plain words with short lines", scores: { adhd: 1, autism: 0, dyslexia: 2, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Lower-intensity wording and softer urgency", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q10",
    text: "What most improves your confidence in an answer?",
    options: [
      { id: "a", label: "Quick takeaway up front", scores: { adhd: 3, autism: 0, dyslexia: 1, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Literal precision and clear constraints", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Reduced reading friction", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "A steady and reassuring tone", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q11",
    text: "How should technical terms be presented?",
    options: [
      { id: "a", label: "Key terms highlighted after a summary", scores: { adhd: 2, autism: 1, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Defined explicitly with no figurative phrasing", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Simplified and split across short lines", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Presented gently to avoid overwhelm", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 2, dyscalculia: 0 } }
    ]
  },
  {
    id: "q12",
    text: "When values are large, what helps most?",
    options: [
      { id: "a", label: "Only the most relevant numbers", scores: { adhd: 1, autism: 1, dyslexia: 1, anxiety: 0, dyscalculia: 1 } },
      { id: "b", label: "Consistent exact numeric notation", scores: { adhd: 0, autism: 2, dyslexia: 0, anxiety: 0, dyscalculia: 1 } },
      { id: "c", label: "Readable formatting and spacing", scores: { adhd: 0, autism: 0, dyslexia: 1, anxiety: 0, dyscalculia: 2 } },
      { id: "d", label: "Relatable comparisons and context", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 0, dyscalculia: 3 } }
    ]
  },
  {
    id: "q13",
    text: "What tone keeps you most productive?",
    options: [
      { id: "a", label: "Focused and concise", scores: { adhd: 2, autism: 1, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Direct and literal", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Simple and easy to scan", scores: { adhd: 1, autism: 0, dyslexia: 2, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Supportive and non-pressuring", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q14",
    text: "If a message has many steps, I prefer...",
    options: [
      { id: "a", label: "A clear ordered list from priority to detail", scores: { adhd: 3, autism: 1, dyslexia: 1, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Explicit rule-by-rule format", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Small sections with one idea at a time", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Less intense language in every step", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  },
  {
    id: "q15",
    text: "Overall, what adaptation would help you most every day?",
    options: [
      { id: "a", label: "Summary-first prioritization", scores: { adhd: 3, autism: 0, dyslexia: 1, anxiety: 0, dyscalculia: 0 } },
      { id: "b", label: "Literal, explicit language", scores: { adhd: 0, autism: 3, dyslexia: 0, anxiety: 0, dyscalculia: 0 } },
      { id: "c", label: "Readability and short sentence flow", scores: { adhd: 1, autism: 0, dyslexia: 3, anxiety: 0, dyscalculia: 0 } },
      { id: "d", label: "Calmer tone and reduced urgency", scores: { adhd: 0, autism: 0, dyslexia: 0, anxiety: 3, dyscalculia: 0 } }
    ]
  }
];

const PROFILE_DESCRIPTIONS: Record<ProfileId, string> = {
  adhd: "Prioritizes summary-first structure and chunked focus-friendly output.",
  autism: "Reduces ambiguity and figurative language for clear literal communication.",
  dyslexia: "Improves readability with shorter sentences and clearer visual flow.",
  anxiety: "Softens urgency and high-pressure phrasing while preserving intent.",
  dyscalculia: "Contextualizes numbers with relatable comparisons and simpler framing."
};

const PROFILE_IMPACT: Record<ProfileId, string[]> = {
  adhd: [
    "Highlights the main point before details.",
    "Breaks long responses into manageable chunks.",
    "Reorders content so priorities are clearer."
  ],
  autism: [
    "Replaces ambiguous or figurative wording.",
    "Prefers direct, explicit statements.",
    "Keeps terminology and logic consistent."
  ],
  dyslexia: [
    "Splits dense sentences into simpler ones.",
    "Increases readability and scanability.",
    "Reduces visual and linguistic friction."
  ],
  anxiety: [
    "Rewrites urgent language into calmer phrasing.",
    "Reduces pressure cues and alarm words.",
    "Maintains supportive, non-urgent tone."
  ],
  dyscalculia: [
    "Adds practical context to percentages and large values.",
    "Converts abstract numbers into relatable comparisons.",
    "Keeps quantitative information easier to interpret."
  ]
};

const PROFILE_EXAMPLE: Record<ProfileId, { before: string; after: string }> = {
  adhd: {
    before: "The report contains multiple sections and detailed caveats before the main recommendation is introduced near the end.",
    after: "Bottom line: use the recommended option first. Details and caveats are listed below in short steps."
  },
  autism: {
    before: "We should move the needle and circle back soon to ensure alignment.",
    after: "We should improve results by 10% and review progress tomorrow."
  },
  dyslexia: {
    before: "This long explanation includes multiple connected clauses and layered qualifiers that are difficult to scan quickly.",
    after: "This explanation is easier to scan. One idea appears in each short sentence."
  },
  anxiety: {
    before: "This is urgent and must be fixed immediately to avoid failure.",
    after: "This is important. Please review when ready so we can stay on track."
  },
  dyscalculia: {
    before: "The budget increased by 38% and now totals $420,000.",
    after: "The budget increased by 38% (about 2 in 5). It now totals $420,000 (around a house deposit scale)."
  }
};

function scoreAnswers(answers: number[]): Record<ProfileId, number> {
  const totals: Record<ProfileId, number> = {
    adhd: 0,
    autism: 0,
    dyslexia: 0,
    anxiety: 0,
    dyscalculia: 0
  };

  QUESTIONS.forEach((question, index) => {
    const selected = Number(answers[index]);
    if (Number.isNaN(selected) || selected < 0 || selected > 3) {
      return;
    }
    const option = question.options[selected];
    if (!option) {
      return;
    }
    profileMap.forEach((profile) => {
      totals[profile] += option.scores[profile] || 0;
    });
  });

  return totals;
}

export async function GET() {
  return NextResponse.json({ questions: QUESTIONS });
}

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => ({}))) as { answers?: number[] };
  const answers = Array.isArray(body.answers) ? body.answers : [];

  if (!answers.length || answers.length < QUESTIONS.length) {
    return NextResponse.json({ error: "answers are required" }, { status: 400 });
  }

  const scores = scoreAnswers(answers);
  const ranking = profileMap
    .map((profile) => ({ profile, score: scores[profile] }))
    .sort((a, b) => b.score - a.score);

  const primary = ranking[0]?.profile ?? "adhd";
  const secondary = ranking[1]?.profile ?? null;

  const top = ranking[0]?.score ?? 0;
  const second = ranking[1]?.score ?? 0;
  const total = Math.max(1, ranking.reduce((acc, item) => acc + item.score, 0));
  const confidence = Math.min(0.95, Math.max(0.5, (top - second + top) / total));

  return NextResponse.json({
    primary_profile: primary,
    secondary_profile: secondary,
    confidence,
    scores,
    description: PROFILE_DESCRIPTIONS[primary],
    impact: PROFILE_IMPACT[primary],
    example: PROFILE_EXAMPLE[primary]
  });
}
