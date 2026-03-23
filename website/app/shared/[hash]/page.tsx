import Link from "next/link";
import { notFound } from "next/navigation";

import { readJsonFile } from "@/lib/serverStore";

type Props = {
  params: { hash: string };
};

type SharedItem = {
  hash: string;
  input: string;
  profile: string;
  adapted: string;
  created_at: string;
};

export default async function SharedPage({ params }: Props) {
  const records = await readJsonFile<Record<string, SharedItem>>("shared.json", {});
  const item = records[params.hash];
  if (!item) {
    notFound();
  }

  return (
    <section className="space-y-6">
      <h1 className="text-4xl font-black text-brand-ink">Shared adaptation</h1>
      <p className="text-sm text-brand-slate">Profile: {item.profile.toUpperCase()}</p>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-black/10 bg-white p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-brand-slate">Original</p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-brand-slate">{item.input}</p>
        </div>
        <div className="rounded-2xl border border-black/10 bg-white p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-brand-slate">Adapted</p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-brand-ink">{item.adapted}</p>
        </div>
      </div>

      <Link
        href="/playground"
        className="inline-flex h-11 items-center rounded-xl bg-brand-primary px-4 text-sm font-semibold text-white"
      >
        Try it yourself
      </Link>
    </section>
  );
}
