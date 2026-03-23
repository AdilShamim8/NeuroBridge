"use client";

import { Copy, Check } from "lucide-react";
import { useState } from "react";

type CodeBlockProps = {
  children: string;
  language?: string;
  showLineNumbers?: boolean;
};

export function CodeBlock({ children, language = "text", showLineNumbers = true }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const lines = children.trimEnd().split("\n");

  async function handleCopy() {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div className="overflow-hidden rounded-xl border border-black/10 bg-brand-ink text-white">
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-2 text-xs">
        <span className="uppercase tracking-wide text-white/70">{language}</span>
        <button onClick={handleCopy} className="inline-flex items-center gap-1 rounded px-2 py-1 hover:bg-white/10">
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />} Copy
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-6">
        {lines.map((line, index) => (
          <div key={`${line}-${index}`} className="whitespace-pre">
            {showLineNumbers ? <span className="mr-3 inline-block w-6 text-right text-white/40">{index + 1}</span> : null}
            <span>{line}</span>
          </div>
        ))}
      </pre>
    </div>
  );
}
