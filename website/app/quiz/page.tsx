"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { FeedbackWidget } from "@/components/FeedbackWidget";
import { trackEvent } from "@/lib/analytics";
import { getQuizQuestions, submitQuiz } from "@/lib/api";

type ProfileId = "adhd" | "autism" | "dyslexia" | "anxiety" | "dyscalculia";

type QuizQuestion = {
  id: string;
  text: string;
  options: Array<{ id: string; label: string }>;
};

type QuizResult = {
  primary_profile: ProfileId;
  secondary_profile?: ProfileId | null;
  confidence: number;
  description: string;
  impact: string[];
  example: { before: string; after: string };
};

const STORAGE_KEY = "nb-quiz-state-v1";

const FALLBACK_QUESTIONS: QuizQuestion[] = Array.from({ length: 15 }, (_, index) => ({
  id: `q${index + 1}`,
  text: `Question ${index + 1}: Which response style helps you most?`,
  options: [
    { id: "a", label: "Summary-first and structured" },
    { id: "b", label: "Literal and explicit" },
    { id: "c", label: "Simple and easy to read" },
    { id: "d", label: "Calm and non-urgent" }
  ]
}));

const PROFILE_LABELS: Record<ProfileId, string> = {
  adhd: "ADHD",
  autism: "Autism",
  dyslexia: "Dyslexia",
  anxiety: "Anxiety",
  dyscalculia: "Dyscalculia"
};

function estimateSecondsRemaining(answered: number, total: number): number {
  const unresolved = Math.max(0, total - answered);
  return Math.max(8, unresolved * 6);
}

function encodeResultShare(profile: ProfileId, confidence: number): string {
  return btoa(unescape(encodeURIComponent(JSON.stringify({ profile, confidence }))));
}

function decodeResultShare(value: string): { profile: ProfileId; confidence: number } | null {
  try {
    const parsed = JSON.parse(decodeURIComponent(escape(atob(value)))) as {
      profile: ProfileId;
      confidence: number;
    };
    if (!parsed.profile || typeof parsed.confidence !== "number") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export default function QuizPage() {
  const reduceMotion = useReducedMotion();
  const [questions, setQuestions] = useState<QuizQuestion[]>(FALLBACK_QUESTIONS);
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<number[]>(Array(15).fill(-1));
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState("");
  const [paused, setPaused] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [userId, setUserId] = useState("");
  const [saveStatus, setSaveStatus] = useState("");

  useEffect(() => {
    void getQuizQuestions()
      .then((payload) => {
        if (payload?.questions?.length) {
          setQuestions(payload.questions);
          setAnswers((prev: number[]) =>
            prev.length === payload.questions.length ? prev : Array(payload.questions.length).fill(-1)
          );
        }
      })
      .catch(() => {
        setQuestions(FALLBACK_QUESTIONS);
      });
  }, []);

  useEffect(() => {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const share = new URLSearchParams(window.location.search).get("result");
      if (!share) {
        return;
      }
      const decoded = decodeResultShare(share);
      if (!decoded) {
        return;
      }
      setResult({
        primary_profile: decoded.profile,
        confidence: decoded.confidence,
        description: "Shared quiz result",
        impact: ["Shared profile view only."],
        example: { before: "", after: "" }
      });
      setStep(16);
      return;
    }

    try {
      const parsed = JSON.parse(raw) as {
        step: number;
        answers: number[];
      };
      if (Array.isArray(parsed.answers)) {
        setAnswers(parsed.answers);
      }
      if (typeof parsed.step === "number") {
        setStep(Math.max(0, Math.min(16, parsed.step)));
      }
    } catch {
      return;
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        step,
        answers
      })
    );
  }, [step, answers]);

  const answeredCount = useMemo(() => answers.filter((v: number) => v >= 0).length, [answers]);
  const currentQuestion = questions[Math.max(0, step - 1)] || null;

  const partialProfile = useMemo(() => {
    if (answeredCount < 8) {
      return null;
    }
    const counters: Record<ProfileId, number> = {
      adhd: 0,
      autism: 0,
      dyslexia: 0,
      anxiety: 0,
      dyscalculia: 0
    };
    answers.forEach((value: number, index: number) => {
      if (value < 0) {
        return;
      }
      if (value === 0) counters.adhd += 1;
      if (value === 1) counters.autism += 1;
      if (value === 2) counters.dyslexia += 1;
      if (value === 3) counters.anxiety += 1;
      if (index % 5 === 2) counters.dyscalculia += value === 3 ? 1 : 0;
    });
    return (Object.entries(counters).sort((a, b) => b[1] - a[1])[0]?.[0] as ProfileId) || null;
  }, [answers, answeredCount]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (step < 1 || step > questions.length || !currentQuestion) {
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        setPaused(!paused);
        return;
      }
      if (paused) {
        return;
      }
      if (/^[1-4]$/.test(event.key)) {
        const selected = Number(event.key) - 1;
        setAnswers((prev: number[]) => {
          const next = [...prev];
          next[step - 1] = selected;
          return next;
        });
      }
      if ((event.key === "Enter" || event.key === " ") && answers[step - 1] >= 0) {
        event.preventDefault();
        if (step < questions.length) {
          setStep(step + 1);
        } else {
          void finishQuiz();
        }
      }
      if (event.key === "Backspace") {
        event.preventDefault();
        setStep((prev: number) => Math.max(0, prev - 1));
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [answers, currentQuestion, paused, questions.length, step]);

  async function finishQuiz() {
    setLoading(true);
    setError("");
    try {
      const payload = (await submitQuiz(answers)) as QuizResult;
      trackEvent("quiz_completed", { profile: payload.primary_profile });
      setResult(payload);
      setStep(16);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Unable to complete quiz right now.");
    } finally {
      setLoading(false);
    }
  }

  async function saveProfile() {
    if (!result || !userId.trim()) {
      return;
    }
    setSaveStatus("Saving...");
    try {
      const response = await fetch("/api/adapt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "Save profile preference",
          profile: result.primary_profile,
          output_format: "plain",
          user_id: userId.trim()
        })
      });
      if (!response.ok) {
        throw new Error("Profile save failed");
      }
      setSaveStatus("Profile saved for this user ID.");
    } catch {
      setSaveStatus("Could not save right now. Please try again.");
    }
  }

  function retakeQuiz() {
    setAnswers(Array(questions.length).fill(-1));
    setStep(0);
    setResult(null);
    setError("");
    setSaveOpen(false);
    setSaveStatus("");
    sessionStorage.removeItem(STORAGE_KEY);
  }

  async function shareResult() {
    if (!result) {
      return;
    }
    const encoded = encodeResultShare(result.primary_profile, result.confidence);
    const url = `${window.location.origin}${window.location.pathname}?result=${encodeURIComponent(encoded)}`;
    await navigator.clipboard.writeText(url);
    setSaveStatus("Share link copied.");
  }

  const progress = Math.round((Math.max(0, step) / Math.max(1, questions.length)) * 100);
  const estimated = estimateSecondsRemaining(answeredCount, questions.length);

  if (step === 0) {
    return (
      <section className="space-y-6">
        <h1 className="text-4xl font-black text-brand-ink">Find your cognitive profile in 2 minutes</h1>
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="badge-pill border border-black/10 bg-white">Not a diagnosis</span>
          <span className="badge-pill border border-black/10 bg-white">Private by default</span>
          <span className="badge-pill border border-black/10 bg-white">Takes ~90 seconds</span>
        </div>
        <p className="max-w-3xl text-lg leading-8 text-brand-slate">
          This quiz helps identify which adaptation style makes AI output easier and more comfortable for you to use.
          You stay in control at every step.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button
            className="h-12 min-w-44 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
            onClick={() => {
              trackEvent("quiz_started");
              setStep(1);
            }}
          >
            Start Quiz
          </Button>
          <Link
            href="/playground"
            className="inline-flex h-12 items-center rounded-xl border border-black/10 px-4 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
          >
            Skip quiz and choose a profile manually
          </Link>
        </div>
        <FeedbackWidget page="quiz" />
      </section>
    );
  }

  if (step === 16 && result) {
    const confidencePct = Math.round(result.confidence * 100);
    const secondaryProfile = result.secondary_profile as ProfileId | null | undefined;
    const secondaryLabel = secondaryProfile ? PROFILE_LABELS[secondaryProfile] : null;
    const primaryLabel = PROFILE_LABELS[result.primary_profile as ProfileId];

    return (
      <section className="space-y-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={primaryLabel}
            initial={{ opacity: 0, y: reduceMotion ? 0 : 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="rounded-2xl border border-black/10 bg-white/85 p-6"
          >
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-brand-slate">Your primary profile</p>
            <h2 className="mt-2 text-4xl font-black text-brand-primary">{primaryLabel}</h2>
            <p className="mt-3 max-w-2xl text-brand-slate">{result.description}</p>
            {secondaryLabel ? <p className="mt-3 text-sm text-brand-ink">You also show traits of {secondaryLabel}.</p> : null}

            <div className="mt-6 flex flex-wrap items-center gap-6">
              <div className="relative h-28 w-28">
                <svg viewBox="0 0 100 100" className="h-28 w-28" aria-label={`Confidence ${confidencePct}%`} role="img">
                  <circle cx="50" cy="50" r="42" stroke="#e8e8f4" strokeWidth="10" fill="none" />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    stroke="#7F77DD"
                    strokeWidth="10"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={`${(confidencePct / 100) * 264} 264`}
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-lg font-black text-brand-ink">{confidencePct}%</div>
              </div>
              <ul className="space-y-2">
                {result.impact.map((point: string) => (
                  <li key={point} className="text-sm text-brand-slate">• {point}</li>
                ))}
              </ul>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl bg-rose-50 p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-rose-700">Before</p>
                <p className="mt-2 text-sm text-brand-slate">{result.example.before}</p>
              </div>
              <div className="rounded-xl bg-emerald-50 p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">After</p>
                <p className="mt-2 text-sm text-brand-ink">{result.example.after}</p>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        <div className="flex flex-wrap gap-3">
          <Link
            href={`/playground?profile=${result.primary_profile}`}
            className="inline-flex h-12 items-center rounded-xl bg-brand-primary px-4 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
          >
            Try it in the Playground
          </Link>
          <button
            onClick={() => setSaveOpen((v) => !v)}
            className="h-12 rounded-xl border border-black/10 px-4 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
          >
            Save my profile
          </button>
          <button
            onClick={shareResult}
            className="h-12 rounded-xl border border-black/10 px-4 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
          >
            Share this quiz
          </button>
        </div>

        {saveOpen ? (
          <div className="rounded-xl border border-black/10 bg-white p-4">
            <label htmlFor="save-user" className="text-sm font-semibold text-brand-slate">User ID</label>
            <div className="mt-2 flex flex-wrap gap-2">
              <input
                id="save-user"
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                className="h-11 min-w-[240px] rounded-xl border border-black/10 px-3 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
                placeholder="your-user-id"
              />
              <button
                onClick={saveProfile}
                className="h-11 rounded-xl bg-brand-secondary px-4 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
              >
                Save
              </button>
            </div>
            {saveStatus ? <p className="mt-2 text-xs text-brand-slate">{saveStatus}</p> : null}
          </div>
        ) : null}

        <button onClick={retakeQuiz} className="text-sm font-semibold text-brand-primary hover:underline">
          Retake quiz
        </button>
        <FeedbackWidget page="quiz" />
      </section>
    );
  }

  return (
    <section className="space-y-5">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm text-brand-slate">
          <span>{Math.min(step, questions.length)}/{questions.length}</span>
          <span>About {estimated} seconds left</span>
        </div>
        <div
          aria-label={`Progress ${progress}%`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
          role="progressbar"
          className="h-3 w-full overflow-hidden rounded-full bg-black/10"
        >
          <div className="h-full bg-brand-primary transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs text-brand-slate">
        <span className="badge-pill border border-black/10 bg-white">1-4: Select option</span>
        <span className="badge-pill border border-black/10 bg-white">Enter: Confirm</span>
        <span className="badge-pill border border-black/10 bg-white">Backspace: Back</span>
        <span className="badge-pill border border-black/10 bg-white">Esc: Pause or resume</span>
      </div>

      {partialProfile ? (
        <div className="rounded-xl border border-brand-primary/25 bg-brand-mist p-3 text-sm text-brand-ink">
          Based on your answers so far, you lean towards {PROFILE_LABELS[partialProfile]}.
        </div>
      ) : null}

      {paused ? (
        <div className="rounded-2xl border border-black/10 bg-white/85 p-6">
          <h2 className="text-2xl font-black text-brand-ink">Quiz paused</h2>
          <p className="mt-2 text-brand-slate">Your progress is saved in this browser session.</p>
          <button
            onClick={() => setPaused(false)}
            className="mt-4 h-12 rounded-xl bg-brand-primary px-4 text-base font-semibold text-white"
          >
            Resume quiz
          </button>
        </div>
      ) : null}

      {!paused ? <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestion?.id || "question"}
          initial={{ opacity: 0, x: reduceMotion ? 0 : 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: reduceMotion ? 0 : -20 }}
          transition={{ duration: 0.22 }}
          className="rounded-2xl border border-black/10 bg-white/85 p-6"
        >
          <h2 className="max-w-3xl text-3xl font-black leading-tight text-brand-ink" aria-live="polite">
            {currentQuestion?.text}
          </h2>

          <div className="mt-5 space-y-3" role="radiogroup" aria-label="Quiz options">
            {currentQuestion?.options.map((option, index) => {
              const selected = answers[step - 1] === index;
              return (
                <button
                  key={option.id}
                  role="radio"
                  aria-checked={selected}
                  aria-label={`Option ${index + 1}: ${option.label}`}
                  onClick={() => {
                      setAnswers((prev: number[]) => {
                      const next = [...prev];
                      next[step - 1] = index;
                      return next;
                    });
                  }}
                  className={`min-h-12 w-full rounded-xl border px-4 py-3 text-left text-base leading-7 transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary ${
                    selected
                      ? "border-brand-primary bg-brand-mist text-brand-ink"
                      : "border-black/10 bg-white text-brand-slate hover:border-brand-primary/40"
                  }`}
                >
                  <span className="mr-2 text-xs font-bold uppercase tracking-wide text-brand-slate">{index + 1}</span>
                  {option.label}
                </button>
              );
            })}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => setStep((prev) => Math.max(0, prev - 1))}
              className="h-12 min-w-28 rounded-xl border border-black/10 px-4 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-primary"
            >
              Back
            </button>
            <Button
              className="h-12 min-w-32"
              onClick={() => {
                if (answers[step - 1] < 0) {
                  setError("Select one option before continuing.");
                  return;
                }
                setError("");
                if (step < questions.length) {
                  setStep(step + 1);
                } else {
                  void finishQuiz();
                }
              }}
              disabled={loading}
            >
              {step < questions.length ? "Next" : loading ? "Calculating..." : "View result"}
            </Button>
          </div>

          {error ? <p role="alert" className="mt-3 text-sm text-rose-700">{error}</p> : null}
        </motion.div>
      </AnimatePresence> : null}
      <FeedbackWidget page="quiz" />
    </section>
  );
}
