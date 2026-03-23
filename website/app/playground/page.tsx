"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { BookOpenText, BrainCircuit, Calculator, Check, Download, Heart, Puzzle, Share2 } from "lucide-react";
import { type ComponentType, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { FeedbackWidget } from "@/components/FeedbackWidget";
import { InlineHelpful } from "@/components/InlineHelpful";
import { Card } from "@/components/ui/card";
import { trackEvent } from "@/lib/analytics";
import { adaptText } from "@/lib/api";
import { summarizeChanges, wordDiff } from "@/lib/diff";

type ProfileId = "adhd" | "autism" | "dyslexia" | "anxiety" | "dyscalculia";
type OutputFormat = "markdown" | "plain" | "html" | "json";
type TabId = "adapted" | "original" | "changed";
type FontSizeOption = "S" | "M" | "L" | "XL";
type LineSpacingOption = "normal" | "relaxed" | "wide";
type FontOption = "default" | "open-dyslexic" | "atkinson";

type ReadingPreferences = {
  fontSize: FontSizeOption;
  lineSpacing: LineSpacingOption;
  font: FontOption;
};

const READING_PREFS_KEY = "nb-reading-preferences-v1";

const SAMPLE_TEXT = `Quantum computing uses qubits instead of regular bits, which means information can exist in several possible states at once before measurement. This allows certain calculations to be explored in parallel, especially for optimization and simulation tasks that are hard for classical systems.

However, qubits are fragile and can lose coherence due to noise, temperature shifts, or interference from nearby systems. Engineers use error correction, precise control signals, and specialized cooling to keep calculations stable enough to complete.

In practical terms, quantum computers are not expected to replace laptops or cloud CPUs for everyday workloads. Instead, they may become specialized accelerators for chemistry simulation, logistics planning, and cryptographic research where probabilistic exploration can produce useful speedups.

A useful mental model is that classical computing checks one path after another, while quantum systems can represent and evaluate many path candidates in a single mathematical space. That does not mean every task becomes faster. Most business workloads still run best on conventional hardware, and current quantum devices remain limited by noise and scale. The near-term opportunity is hybrid workflows where classical systems orchestrate reliable steps while quantum processors are used for a narrow, high-value part of a pipeline.`;

const PROFILE_OPTIONS: Array<{
  id: ProfileId;
  label: string;
  tooltip: string;
  icon: ComponentType<{ className?: string }>;
}> = [
  { id: "adhd", label: "ADHD", tooltip: "Summary-first chunks with clearer priority cues.", icon: BrainCircuit },
  { id: "autism", label: "Autism", tooltip: "More literal wording with less ambiguity.", icon: Puzzle },
  { id: "dyslexia", label: "Dyslexia", tooltip: "Shorter lines and improved readability flow.", icon: BookOpenText },
  { id: "anxiety", label: "Anxiety", tooltip: "Calmer phrasing and urgency softening.", icon: Heart },
  { id: "dyscalculia", label: "Dyscalculia", tooltip: "Numbers reframed with practical context.", icon: Calculator }
];

const SHOWCASE = [
  {
    title: "ADHD: Structure overload",
    profile: "adhd" as ProfileId,
    input:
      "There are seven major considerations, each with dependencies and caveats, and the final recommendation appears only after background context and exception handling notes.",
    output: "Bottom line: Start with the final recommendation. Then review seven considerations in short chunks."
  },
  {
    title: "Dyslexia: Dense sentence",
    profile: "dyslexia" as ProfileId,
    input:
      "The migration process involves collecting requirements, sequencing tasks, validating dependencies, coordinating approvals, and preparing fallback plans in one long explanation.",
    output: "The migration process has five steps. Collect requirements. Sequence tasks. Validate dependencies. Coordinate approvals. Prepare fallback plans."
  },
  {
    title: "Anxiety: High-pressure tone",
    profile: "anxiety" as ProfileId,
    input: "This is urgent. You must send the patch immediately or the release will fail.",
    output: "This is important. Please send the patch when ready so the release stays on track."
  }
];

function markdownToHtml(markdown: string): string {
  return markdown
    .replace(/^### (.*)$/gim, "<h3>$1</h3>")
    .replace(/^## (.*)$/gim, "<h2>$1</h2>")
    .replace(/^# (.*)$/gim, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/gim, "<em>$1</em>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br />");
}

function encodeShare(text: string, profile: ProfileId): string {
  const payload = JSON.stringify({ text, profile });
  return btoa(unescape(encodeURIComponent(payload)));
}

function decodeShare(value: string): { text: string; profile: ProfileId } | null {
  try {
    const parsed = JSON.parse(decodeURIComponent(escape(atob(value)))) as {
      text: string;
      profile: ProfileId;
    };
    if (!parsed.text || !parsed.profile) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export default function PlaygroundPage() {
  const reduceMotion = useReducedMotion();
  const [input, setInput] = useState("");
  const [profile, setProfile] = useState<ProfileId>("adhd");
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("markdown");
  const [userId, setUserId] = useState("");
  const [showUserId, setShowUserId] = useState(false);
  const [tab, setTab] = useState<TabId>("adapted");
  const [adaptedText, setAdaptedText] = useState("");
  const [modulesRun, setModulesRun] = useState<string[]>([]);
  const [processingMs, setProcessingMs] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [successTick, setSuccessTick] = useState(0);
  const [sharedAdaptationUrl, setSharedAdaptationUrl] = useState("");
  const [prefsOpen, setPrefsOpen] = useState(false);
  const [readingPrefs, setReadingPrefs] = useState<ReadingPreferences>({
    fontSize: "M",
    lineSpacing: "normal",
    font: "default"
  });
  const outputRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    setInput(SAMPLE_TEXT);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem(READING_PREFS_KEY);
    if (!saved) {
      return;
    }
    try {
      const parsed = JSON.parse(saved) as ReadingPreferences;
      if (parsed.fontSize && parsed.lineSpacing && parsed.font) {
        setReadingPrefs(parsed);
      }
    } catch {
      return;
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(READING_PREFS_KEY, JSON.stringify(readingPrefs));
  }, [readingPrefs]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const encoded = params.get("demo");
    if (!encoded) {
      return;
    }
    const decoded = decodeShare(encoded);
    if (!decoded) {
      return;
    }
    setInput(decoded.text);
    setProfile(decoded.profile);
  }, []);

  useEffect(() => {
    const area = textareaRef.current;
    if (!area) {
      return;
    }
    area.style.height = "auto";
    area.style.height = `${Math.max(120, area.scrollHeight)}px`;
  }, [input]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const isMeta = event.metaKey || event.ctrlKey;
      if (isMeta && event.key.toLowerCase() === "enter") {
        event.preventDefault();
        void runAdapt();
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        setAdaptedText("");
        setModulesRun([]);
        setProcessingMs(0);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const diff = useMemo(() => wordDiff(input, adaptedText), [input, adaptedText]);
  const summary = useMemo(() => summarizeChanges(input, adaptedText), [input, adaptedText]);
  const characterCount = input.length;
  const readingStyle = useMemo(
    () => {
      const fontSize =
        readingPrefs.fontSize === "S"
          ? "16px"
          : readingPrefs.fontSize === "L"
            ? "19px"
            : readingPrefs.fontSize === "XL"
              ? "21px"
              : "17px";

      const lineHeight =
        readingPrefs.lineSpacing === "relaxed" ? 1.8 : readingPrefs.lineSpacing === "wide" ? 2 : 1.6;

      const fontFamily =
        readingPrefs.font === "open-dyslexic"
          ? '"OpenDyslexic", "Open Dyslexic", Inter, system-ui, sans-serif'
          : readingPrefs.font === "atkinson"
            ? '"Atkinson Hyperlegible", Inter, system-ui, sans-serif'
            : "Inter, system-ui, sans-serif";

      return {
        fontSize,
        lineHeight,
        fontFamily
      };
    },
    [readingPrefs]
  );

  async function runAdapt() {
    if (!input.trim()) {
      setError("Paste or load text first, then adapt.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await adaptText({
        text: input,
        profile,
        output_format: outputFormat,
        user_id: userId || undefined
      });
      trackEvent("playground_adapt", { profile, format: outputFormat });
      setAdaptedText(response.adapted_text);
      setModulesRun(response.modules_run || []);
      setProcessingMs(response.processing_ms || 0);
      setSuccessTick(successTick + 1);
      if (window.matchMedia("(max-width: 1024px)").matches) {
        outputRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Something went wrong while adapting text.");
    } finally {
      setLoading(false);
    }
  }

  async function copyOutput() {
    if (!adaptedText) {
      return;
    }
    await navigator.clipboard.writeText(adaptedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  function downloadOutput() {
    if (!adaptedText) {
      return;
    }
    const ext = outputFormat === "markdown" ? "md" : "txt";
    const blob = new Blob([adaptedText], { type: "text/plain;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `neurobridge-output.${ext}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
  }

  async function shareDemo() {
    const encoded = encodeShare(input, profile);
    const shareUrl = `${window.location.origin}${window.location.pathname}?demo=${encodeURIComponent(encoded)}`;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  }

  async function shareAdaptation() {
    if (!adaptedText.trim()) {
      return;
    }
    const response = await fetch("/api/shared", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        input,
        profile,
        adapted: adaptedText
      })
    });
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { url?: string };
    if (!payload.url) {
      return;
    }
    const url = `${window.location.origin}${payload.url}`;
    setSharedAdaptationUrl(url);
    await navigator.clipboard.writeText(url);
  }

  function loadShowcase(index: number) {
    const sample = SHOWCASE[index];
    setInput(sample.input);
    setProfile(sample.profile);
    setAdaptedText(sample.output);
    setTab("adapted");
    setModulesRun(["Chunker", sample.profile === "anxiety" ? "UrgencyFilter" : "SentenceSimplifier"]);
    setProcessingMs(7);
  }

  return (
    <section className="space-y-8 pb-8" style={readingStyle}>
      <div>
        <h1 className="text-4xl font-black text-brand-ink md:text-5xl">Playground</h1>
        <p className="mt-2 max-w-3xl text-brand-slate">
          Paste any AI output, select a profile, and instantly feel how NeuroBridge transforms clarity, tone, and cognitive load.
        </p>
        <button
          onClick={() => setPrefsOpen(!prefsOpen)}
          className="mt-3 rounded-lg border border-black/10 bg-white px-3 py-2 text-sm font-semibold"
        >
          Reading preferences
        </button>
        {prefsOpen ? (
          <div className="mt-3 grid gap-3 rounded-xl border border-black/10 bg-white/85 p-3 sm:grid-cols-3">
            <label className="text-sm text-brand-slate">
              Font size
              <select
                className="mt-1 h-11 w-full rounded-lg border border-black/10 bg-white px-2"
                value={readingPrefs.fontSize}
                onChange={(event: any) => setReadingPrefs({ ...readingPrefs, fontSize: event.target.value as FontSizeOption })}
              >
                <option value="S">S</option>
                <option value="M">M</option>
                <option value="L">L</option>
                <option value="XL">XL</option>
              </select>
            </label>
            <label className="text-sm text-brand-slate">
              Line spacing
              <select
                className="mt-1 h-11 w-full rounded-lg border border-black/10 bg-white px-2"
                value={readingPrefs.lineSpacing}
                onChange={(event: any) => setReadingPrefs({ ...readingPrefs, lineSpacing: event.target.value as LineSpacingOption })}
              >
                <option value="normal">Normal</option>
                <option value="relaxed">Relaxed</option>
                <option value="wide">Wide</option>
              </select>
            </label>
            <label className="text-sm text-brand-slate">
              Font
              <select
                className="mt-1 h-11 w-full rounded-lg border border-black/10 bg-white px-2"
                value={readingPrefs.font}
                onChange={(event: any) => setReadingPrefs({ ...readingPrefs, font: event.target.value as FontOption })}
              >
                <option value="default">Default</option>
                <option value="open-dyslexic">OpenDyslexic</option>
                <option value="atkinson">Atkinson Hyperlegible</option>
              </select>
            </label>
          </div>
        ) : null}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="space-y-4">
          <label htmlFor="playground-input" className="text-sm font-bold text-brand-slate">
            Paste any AI output here
          </label>
          <textarea
            ref={textareaRef}
            id="playground-input"
            value={input}
            onChange={(event: any) => setInput(event.target.value)}
            placeholder={SAMPLE_TEXT}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "playground-error" : undefined}
            className="min-h-[120px] w-full resize-none rounded-xl border border-black/10 p-4 text-sm leading-7 outline-none ring-brand-primary/50 transition focus:ring-2"
          />
          <div className="flex items-center justify-between text-xs text-brand-slate">
            <button className="font-semibold text-brand-primary hover:underline" onClick={() => setInput(SAMPLE_TEXT)}>
              Use sample text
            </button>
            <span>{characterCount.toLocaleString()} chars</span>
          </div>

          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-brand-slate">Profile</p>
            <div className="overflow-x-auto pb-1">
              <div className="inline-flex min-w-max gap-2">
              {PROFILE_OPTIONS.map((item) => {
                const Icon = item.icon;
                const active = profile === item.id;
                return (
                  <button
                    key={item.id}
                    title={item.tooltip}
                    onClick={() => {
                      setProfile(item.id);
                      trackEvent("profile_selected", { profile: item.id });
                    }}
                    className={`inline-flex items-center gap-1 rounded-full border px-3 py-2 text-xs font-semibold transition ${
                      active
                        ? "border-brand-primary bg-brand-primary text-white"
                        : "border-black/10 bg-white text-brand-ink hover:border-brand-primary/50"
                    }`}
                  >
                    <Icon className="h-4 w-4" /> {item.label}
                  </button>
                );
              })}
              </div>
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-brand-slate">Output format</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {(["markdown", "plain", "html", "json"] as OutputFormat[]).map((format) => (
                <button
                  key={format}
                  onClick={() => setOutputFormat(format)}
                  className={`rounded-lg border px-3 py-2 text-xs font-semibold ${
                    outputFormat === format
                      ? "border-brand-secondary bg-brand-secondary text-white"
                      : "border-black/10 bg-white hover:border-brand-secondary/50"
                  }`}
                >
                  {format === "plain" ? "Plain Text" : format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div>
            <button
              onClick={() => setShowUserId(!showUserId)}
              className="text-xs font-semibold text-brand-primary hover:underline"
            >
              {showUserId ? "Hide profile save" : "Save my profile"}
            </button>
            {showUserId ? (
              <input
                type="text"
                value={userId}
                onChange={(event: any) => setUserId(event.target.value)}
                placeholder="Optional user ID"
                className="mt-2 h-11 w-full rounded-xl border border-black/10 px-3 text-sm outline-none ring-brand-primary/50 focus:ring-2"
              />
            ) : null}
          </div>

          <Button className="h-12 w-full text-base" onClick={runAdapt}>
            Adapt Text
          </Button>
          <div className="flex flex-wrap gap-2 text-xs text-brand-slate">
            <span className="badge-pill border border-black/10 bg-white">Ctrl/Cmd + Enter: Adapt</span>
            <span className="badge-pill border border-black/10 bg-white">Esc: Clear output</span>
          </div>
        </Card>

        <Card ref={outputRef as never} className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="inline-flex rounded-xl border border-black/10 bg-white p-1">
              {([
                ["adapted", "Adapted Output"],
                ["original", "Original"],
                ["changed", "What Changed"]
              ] as Array<[TabId, string]>).map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                    tab === id ? "bg-brand-ink text-white" : "text-brand-slate"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <button onClick={copyOutput} aria-label="Copy output" className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold hover:bg-black/5" title="Copy output">
                {copied ? <span className="inline-flex items-center gap-1"><Check className="h-4 w-4 text-brand-secondary" /> Copied</span> : <span>Copy output</span>}
              </button>
              <button onClick={downloadOutput} aria-label="Download output" className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold hover:bg-black/5" title="Download output">
                <span className="inline-flex items-center gap-1"><Download className="h-4 w-4" /> Download</span>
              </button>
              <button onClick={shareDemo} aria-label="Share demo link" className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold hover:bg-black/5" title="Share demo link">
                <span className="inline-flex items-center gap-1"><Share2 className="h-4 w-4" /> Share demo</span>
              </button>
            </div>
          </div>

          {loading ? (
            <div className="space-y-3">
              <div className="shimmer h-5 w-5/6 rounded" />
              <div className="shimmer h-5 w-4/6 rounded" />
              <div className="shimmer h-5 w-3/6 rounded" />
              <div className="shimmer h-24 rounded-xl" />
            </div>
          ) : null}

          {error ? (
            <div id="playground-error" role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
              We could not adapt that text right now. {error}
            </div>
          ) : null}

          {!loading && !error ? (
            <AnimatePresence mode="wait">
              <motion.div
                key={`${tab}-${successTick}`}
                initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 5, scale: 0.995 }}
                animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
                exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -4 }}
                transition={{ duration: 0.2 }}
                className="min-h-[240px] rounded-xl border border-black/10 bg-white p-4"
                aria-live="polite"
              >
                {tab === "adapted" ? (
                  <div className="text-sm leading-7 text-brand-ink">
                    {outputFormat === "html" ? (
                      <div dangerouslySetInnerHTML={{ __html: adaptedText || "<p>Adapted output will appear here.</p>" }} />
                    ) : outputFormat === "json" ? (
                      <pre className="overflow-x-auto rounded-lg bg-brand-ink p-4 font-mono text-xs text-white">
                        {adaptedText || "{\n  \"adapted\": \"\"\n}"}
                      </pre>
                    ) : outputFormat === "markdown" ? (
                      <div dangerouslySetInnerHTML={{ __html: `<p>${markdownToHtml(adaptedText || "Adapted output will appear here.")}</p>` }} />
                    ) : (
                      <p className="whitespace-pre-wrap">{adaptedText || "Adapted output will appear here."}</p>
                    )}
                  </div>
                ) : null}

                {tab === "original" ? (
                  <p className="whitespace-pre-wrap text-sm leading-7 text-brand-slate">{input || "Original input will appear here."}</p>
                ) : null}

                {tab === "changed" ? (
                  <div className="space-y-3">
                    <p className="text-xs font-semibold text-brand-slate">
                      {summary.wordsSimplified} words simplified · {summary.chunksCreated} chunks created · {summary.urgencySoftened} urgency phrases softened
                    </p>
                    <div className="max-h-[260px] overflow-y-auto rounded-lg bg-slate-50 p-3 text-sm leading-7">
                      {diff.map((token, index) => (
                        <span
                          key={`${token.value}-${index}`}
                          className={
                            token.type === "removed"
                              ? "mr-1 rounded bg-gray-200 px-1 text-gray-500 line-through"
                              : token.type === "added"
                                ? "mr-1 rounded bg-emerald-200 px-1 text-emerald-900"
                                : "mr-1"
                          }
                        >
                          {token.value}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </motion.div>
            </AnimatePresence>
          ) : null}

          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wide text-brand-slate">Transforms applied</p>
            <div className="flex flex-wrap gap-2">
              {(modulesRun.length ? modulesRun : ["Chunker", "SentenceSimplifier", "ToneRewriter"]).map((name) => (
                <span key={name} className="badge-pill border border-brand-primary/25 bg-brand-mist text-brand-ink">
                  {name}
                </span>
              ))}
            </div>
            <p className="text-xs text-brand-slate">Adapted in {Math.round(processingMs || 8)}ms</p>
            <div className="pt-1">
              <button
                onClick={shareAdaptation}
                className="rounded-lg border border-black/10 bg-white px-3 py-2 text-xs font-semibold hover:border-brand-primary/40"
              >
                Share this adaptation
              </button>
              {sharedAdaptationUrl ? <p className="mt-1 text-xs text-brand-slate">Copied: {sharedAdaptationUrl}</p> : null}
            </div>
            {profile === "anxiety" ? <InlineHelpful page="playground" profile={profile} /> : null}
          </div>
        </Card>
      </div>

      <section className="space-y-3 rounded-2xl border border-black/10 bg-white/80 p-6">
        <h2 className="text-2xl font-black text-brand-ink">Before vs After showcase</h2>
        <p className="text-sm text-brand-slate">Load any example to instantly populate the playground with a dramatic transformation.</p>
        <div className="grid gap-4 md:grid-cols-3">
          {SHOWCASE.map((item, index) => (
            <button
              key={item.title}
              onClick={() => loadShowcase(index)}
              className="rounded-xl border border-black/10 bg-white p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <p className="text-xs font-bold uppercase tracking-wide text-brand-secondary">{item.title}</p>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                <div className="rounded-lg bg-rose-50 p-2">
                  <p className="text-[10px] font-bold uppercase tracking-wide text-rose-700">Before</p>
                  <p className="mt-1 line-clamp-4 text-xs text-brand-slate">{item.input}</p>
                </div>
                <div className="rounded-lg bg-emerald-50 p-2">
                  <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700">After</p>
                  <p className="mt-1 line-clamp-4 text-xs font-semibold text-brand-ink">{item.output}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>
      <FeedbackWidget page="playground" profile={profile} />
    </section>
  );
}
