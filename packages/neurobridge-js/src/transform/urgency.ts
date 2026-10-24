export const URGENCY_WORDS = [
  "asap",
  "immediately",
  "urgent",
  "critical",
  "must",
  "right now",
  "at once",
  "without delay",
  "deadline",
  "hurry",
  "rush",
  "emergency",
  "mandatory"
];

export const IDIOM_MAP: Record<string, string> = {
  "bite the bullet": "do the difficult thing",
  "break a leg": "good luck",
  "hit the ground running": "start working immediately",
  "ball park figure": "rough estimate",
  "touch base": "make contact",
  "spill the beans": "share the secret",
  "piece of cake": "very easy task",
  "costs an arm and a leg": "is very expensive",
  "under the weather": "feeling unwell",
  "on the same page": "in agreement",
  "let the cat out of the bag": "reveal a secret",
  "elephant in the room": "obvious issue being ignored"
};

/**
 * Word-specific anxiety softening, mirroring the Python pipeline's
 * _ANXIETY_REPLACEMENTS and _CATASTROPHIC_REPLACEMENTS. Each urgency term
 * maps to a calm replacement that keeps the sentence grammatical - a single
 * blanket replacement ("must" -> "important") produced output like
 * "You important complete this".
 */
export const ANXIETY_REPLACEMENTS: Record<string, string> = {
  asap: "when you have time",
  immediately: "when ready",
  critical: "important",
  urgent: "worth noting",
  must: "consider",
  deadline: "target date",
  failure: "setback",
  problem: "situation",
  error: "issue to address"
};

export const CATASTROPHIC_REPLACEMENTS: Record<string, string> = {
  "this will break": "this might need attention",
  "you must fix": "it is worth looking at",
  "this is wrong": "this could be improved"
};
