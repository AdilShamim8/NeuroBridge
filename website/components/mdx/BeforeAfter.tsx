type BeforeAfterProps = {
  before: string;
  after: string;
};

export function BeforeAfter({ before, after }: BeforeAfterProps) {
  return (
    <div className="my-6 grid gap-3 md:grid-cols-2">
      <div className="rounded-xl bg-rose-50 p-4">
        <p className="text-xs font-bold uppercase tracking-wide text-rose-700">Before</p>
        <p className="mt-2 whitespace-pre-wrap text-sm text-brand-slate">{before}</p>
      </div>
      <div className="rounded-xl bg-emerald-50 p-4">
        <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">After</p>
        <p className="mt-2 whitespace-pre-wrap text-sm text-brand-ink">{after}</p>
      </div>
    </div>
  );
}
